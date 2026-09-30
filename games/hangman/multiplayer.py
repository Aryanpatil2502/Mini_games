import random
import string
import time
from flask import session, request
from flask_socketio import emit, join_room as socketio_join_room

from .logic import new_hangman_game

rooms = {}
sid_to_room = {}

WINS_NEEDED = 2  
ROUND_TIME_LIMIT = 240


def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))


def _display_word(word, guessed_letters):
    return "".join(
        letter if letter in guessed_letters else "_"
        for letter in word
    )


def _is_solved(word, guessed_letters):
    return all(letter in guessed_letters for letter in word)


def _other_player(room, username):
    for p in room["players"]:
        if p != username:
            return p
    return None


def start_new_game(room):
    game = new_hangman_game()

    room["word"] = game["word"]
    room["max_incorrect_guesses"] = game["max_incorrect_guesses"]
    room["game_over"] = False
    room["round_start_time"] = time.time()
    room["round_id"] = room.get("round_id", 0) + 1

    room["player_states"] = {
        p: {
            "guessed_letters": [],
            "incorrect_guesses": 0,
            "status": "playing"  
        }
        for p in room["players"]
    }


def _own_state_payload(room, username):
    state = room["player_states"][username]

    return {
        "display_word": _display_word(room["word"], state["guessed_letters"]),
        "guessed_letters": state["guessed_letters"],
        "incorrect_guesses": state["incorrect_guesses"],
        "max_incorrect_guesses": room["max_incorrect_guesses"],
        "status": state["status"]
    }


def _opponent_state_payload(room, opponent_username):
    state = room["player_states"][opponent_username]

    return {
        "incorrect_guesses": state["incorrect_guesses"],
        "max_incorrect_guesses": room["max_incorrect_guesses"],
        "status": state["status"]
    }


def _personal_payload(room, username, extra):

    opponent = _other_player(room, username)

    payload = {
        "my_state": _own_state_payload(room, username),
        "wins": room["wins"],
        "round_time_limit": ROUND_TIME_LIMIT,
        "round_start_time": room["round_start_time"]
    }

    if opponent is not None:
        payload["opponent_state"] = _opponent_state_payload(room, opponent)

    payload.update(extra)

    return payload


def _emit_to_player(room, username, event, extra):
    sid = room["sids"].get(username)

    if sid is None:
        return

    emit(event, _personal_payload(room, username, extra), room=sid)


def _emit_to_both(room, event, extra):
    for p in room["players"]:
        _emit_to_player(room, p, event, extra)


def _finish_round(room, code, socketio, timed_out_players=None):

    if timed_out_players:
        for p in timed_out_players:
            state = room["player_states"][p]
            if state["status"] == "playing":
                state["status"] = "lost"

    statuses = {p: room["player_states"][p]["status"] for p in room["players"]}

    round_winner = None  # username, or "draw", or None (round still ongoing)

    won_players = [p for p, s in statuses.items() if s == "won"]
    lost_players = [p for p, s in statuses.items() if s == "lost"]

    if won_players:
        round_winner = won_players[0]
    elif len(lost_players) == len(room["players"]):
        round_winner = "draw"
    elif len(lost_players) == 1 and len(room["players"]) - len(lost_players) == 1:
        # One player lost, the other is still playing - round isn't over yet
        return False

    if round_winner is None:
        return False

    room["game_over"] = True

    match_over = False

    if round_winner != "draw":
        room["wins"][round_winner] += 1

        if max(room["wins"].values()) >= WINS_NEEDED:
            match_over = True
            room["closed"] = True

    _emit_to_both(room, 'hangman_guess_result', {
        "round_over": True,
        "round_winner": round_winner,
        "match_over": match_over,
        "word": room["word"]
    })

    if not match_over:
        start_new_game(room)

        _emit_to_both(room, 'hangman_new_game', {})

        socketio.start_background_task(_round_timer, socketio, code, room["round_id"])

    return True


def _round_timer(socketio, code, round_id):
    socketio.sleep(ROUND_TIME_LIMIT)

    room = rooms.get(code)

    if room is None or room["closed"] or room["game_over"]:
        return

    if room.get("round_id") != round_id:
        return  # a newer round has already started

    still_playing = [
        p for p in room["players"]
        if room["player_states"][p]["status"] == "playing"
    ]

    if not still_playing:
        return

    _finish_round(room, code, socketio, timed_out_players=still_playing)


def register_hangman_multiplayer(socketio):

    @socketio.on('hangman_create_room')
    def handle_create_room(data=None):

        if "user_id" not in session:
            emit('hangman_join_error', {"error": "Not logged in"})
            return

        code = generate_code()

        while code in rooms:
            code = generate_code()

        rooms[code] = {
            "players": [],
            "sids": {},
            "word": None,
            "max_incorrect_guesses": 6,
            "player_states": {},
            "wins": {},
            "round_start_time": None,
            "round_id": 0,
            "game_over": False,
            "closed": False
        }

        emit('hangman_room_created', {"code": code})


    @socketio.on('hangman_join_room')
    def handle_join_room(data):

        if "user_id" not in session:
            emit('hangman_join_error', {"error": "Not logged in"})
            return

        code = str(data.get("code", "")).strip().upper()

        if code not in rooms:
            emit('hangman_join_error', {"error": "Room not found"})
            return

        room = rooms[code]

        if room["closed"]:
            emit('hangman_join_error', {"error": "This room has ended"})
            return

        username = session.get("username", "Unknown")

        if username in room["players"]:
            socketio_join_room(code)
            sid_to_room[request.sid] = code
            room["sids"][username] = request.sid

            emit('hangman_joined', {"code": code})

            if len(room["players"]) == 2:
                _emit_to_player(room, username, 'hangman_match_ready', {
                    "players": room["players"],
                    "wins_needed": WINS_NEEDED
                })
            return

        if len(room["players"]) >= 2:
            emit('hangman_join_error', {"error": "Room is full"})
            return

        room["players"].append(username)
        room["wins"][username] = 0

        socketio_join_room(code)
        sid_to_room[request.sid] = code
        room["sids"][username] = request.sid

        emit('hangman_joined', {"code": code})

        if len(room["players"]) == 2:

            start_new_game(room)

            _emit_to_both(room, 'hangman_match_ready', {
                "players": room["players"],
                "wins_needed": WINS_NEEDED
            })

            socketio.start_background_task(_round_timer, socketio, code, room["round_id"])


    @socketio.on('hangman_guess_letter')
    def handle_guess_letter(data):

        if "user_id" not in session:
            return

        code = data.get("code")
        letter = data.get("letter")

        if code not in rooms:
            return

        if not isinstance(letter, str) or len(letter) != 1 or not letter.isalpha():
            return

        letter = letter.lower()

        room = rooms[code]

        if room["closed"] or room["game_over"]:
            return

        username = session.get("username", "Unknown")

        if len(room["players"]) < 2 or username not in room["players"]:
            return

        state = room["player_states"][username]

        if state["status"] != "playing":
            return

        if letter in state["guessed_letters"]:
            return

        state["guessed_letters"].append(letter)

        if letter not in room["word"]:
            state["incorrect_guesses"] += 1

        if _is_solved(room["word"], state["guessed_letters"]):
            state["status"] = "won"
        elif state["incorrect_guesses"] >= room["max_incorrect_guesses"]:
            state["status"] = "lost"

        round_finished = False

        if state["status"] in ("won", "lost"):
            round_finished = _finish_round(room, code, socketio)

        if not round_finished:
            _emit_to_both(room, 'hangman_guess_result', {
                "round_over": False,
                "round_winner": None,
                "match_over": False,
                "word": None
            })


    @socketio.on('disconnect')
    def handle_disconnect():

        code = sid_to_room.pop(request.sid, None)

        if code is None or code not in rooms:
            return

        room = rooms[code]

        if room["closed"]:
            return

        username = session.get("username", "Unknown")

        if username not in room["players"]:
            return

        room["closed"] = True

        remaining = [p for p in room["players"] if p != username]

        if remaining:
            winner = remaining[0]
            winner_sid = room["sids"].get(winner)
            if winner_sid is not None:
                emit('hangman_opponent_left', {"winner": winner}, room=winner_sid)


    @socketio.on('hangman_restart_request')
    def handle_restart_request(data):

        if "user_id" not in session:
            return

        code = data.get("code")

        if code not in rooms:
            emit('hangman_join_error', {"error": "Room not found"})
            return

        room = rooms[code]
        username = session.get("username", "Unknown")

        if username not in room["players"]:
            return

        if len(room["players"]) < 2:
            emit('hangman_join_error', {"error": "Your opponent left"})
            return

        other = _other_player(room, username)
        other_sid = room["sids"].get(other)

        if other_sid is not None:
            emit('hangman_restart_requested', {"from": username}, room=other_sid)


    @socketio.on('hangman_restart_response')
    def handle_restart_response(data):

        if "user_id" not in session:
            return

        code = data.get("code")
        accepted = data.get("accepted")

        if code not in rooms:
            return

        room = rooms[code]
        username = session.get("username", "Unknown")

        if username not in room["players"]:
            return

        if not accepted:
            other = _other_player(room, username)
            other_sid = room["sids"].get(other)
            if other_sid is not None:
                emit('hangman_restart_declined', {"by": username}, room=other_sid)
            return

        room["wins"] = {p: 0 for p in room["players"]}
        room["closed"] = False

        start_new_game(room)

        _emit_to_both(room, 'hangman_match_ready', {
            "players": room["players"],
            "wins_needed": WINS_NEEDED
        })

        socketio.start_background_task(_round_timer, socketio, code, room["round_id"])