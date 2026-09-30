import random
import string
from flask import session, request
from flask_socketio import emit, join_room as socketio_join_room

from .logic import new_memory_game

rooms = {}
sid_to_room = {}

WINS_NEEDED = 5


def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))


def flip_card(cards, flipped, index):

    if cards[index]["matched"]:
        return cards, flipped, False

    if index in flipped:
        return cards, flipped, False

    flipped = flipped + [index]
    matched_pair = False

    if len(flipped) == 2:
        first = flipped[0]
        second = flipped[1]

        if cards[first]["value"] == cards[second]["value"]:
            cards[first]["matched"] = True
            cards[second]["matched"] = True
            matched_pair = True
            flipped = []

    return cards, flipped, matched_pair


def start_new_game(room):
    game = new_memory_game()

    room["cards"] = game["cards"]
    room["flipped"] = []
    room["pairs_found"] = {p: 0 for p in room["players"]}
    room["current_turn"] = room["players"][room["starting_player_index"]]


def _other_player(room, username):
    for p in room["players"]:
        if p != username:
            return p
    return None


def _finish_game(room):
    """
    Called when all 8 pairs have been found in the current game.
    Awards a game-win (or draw). Does NOT reset the board, so the
    finished board can still be sent to the players first.

    Returns True if the whole match just ended, False otherwise.
    """

    players = room["players"]
    p1, p2 = players[0], players[1]

    pairs1 = room["pairs_found"][p1]
    pairs2 = room["pairs_found"][p2]

    if pairs1 > pairs2:
        room["wins"][p1] += 1
    elif pairs2 > pairs1:
        room["wins"][p2] += 1
    # else: tie, no one gets a point

    match_over = max(room["wins"].values()) >= WINS_NEEDED

    if match_over:
        room["closed"] = True

    return match_over


def register_memory_multiplayer(socketio):

    @socketio.on('memory_create_room')
    def handle_create_room(data=None):

        if "user_id" not in session:
            emit('memory_join_error', {"error": "Not logged in"})
            return

        code = generate_code()

        while code in rooms:
            code = generate_code()

        rooms[code] = {
            "players": [],
            "cards": [],
            "flipped": [],
            "pairs_found": {},
            "current_turn": None,
            "wins": {},
            "starting_player_index": 0,
            "closed": False
        }

        emit('memory_room_created', {"code": code})


    @socketio.on('memory_join_room')
    def handle_join_room(data):

        if "user_id" not in session:
            emit('memory_join_error', {"error": "Not logged in"})
            return

        code = str(data.get("code", "")).strip().upper()

        if code not in rooms:
            emit('memory_join_error', {"error": "Room not found"})
            return

        room = rooms[code]

        if room["closed"]:
            emit('memory_join_error', {"error": "This room has ended"})
            return

        username = session.get("username", "Unknown")

        if username in room["players"]:
            socketio_join_room(code)
            sid_to_room[request.sid] = code

            emit('memory_joined', {"code": code})

            if len(room["players"]) == 2:
                emit('memory_match_ready', {
                    "players": room["players"],
                    "wins": room["wins"],
                    "wins_needed": WINS_NEEDED,
                    "cards": room["cards"],
                    "current_turn": room["current_turn"]
                })
            return

        if len(room["players"]) >= 2:
            emit('memory_join_error', {"error": "Room is full"})
            return

        room["players"].append(username)
        room["wins"][username] = 0

        socketio_join_room(code)
        sid_to_room[request.sid] = code

        emit('memory_joined', {"code": code})

        if len(room["players"]) == 2:

            start_new_game(room)

            emit('memory_match_ready', {
                "players": room["players"],
                "wins": room["wins"],
                "wins_needed": WINS_NEEDED,
                "cards": room["cards"],
                "current_turn": room["current_turn"]
            }, room=code)


    @socketio.on('memory_flip_card')
    def handle_flip_card(data):

        if "user_id" not in session:
            return

        code = data.get("code")
        index = data.get("index")

        if code not in rooms:
            return

        room = rooms[code]

        if room["closed"]:
            return

        username = session.get("username", "Unknown")

        if len(room["players"]) < 2 or username not in room["players"]:
            return

        if room["current_turn"] != username:
            return

        if len(room["flipped"]) == 2:
            return

        if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index <= 15:
            return

        cards, flipped, matched_pair = flip_card(
            room["cards"], room["flipped"], index
        )

        room["cards"] = cards
        room["flipped"] = flipped

        game_over = False
        match_over = False

        if matched_pair:
            room["pairs_found"][username] += 1

            total_found = sum(room["pairs_found"].values())

            if total_found == 8:
                game_over = True
                match_over = _finish_game(room)

            # Match: same player continues - current_turn unchanged

        emit('memory_flip_result', {
            "cards": room["cards"],
            "flipped": room["flipped"],
            "current_turn": room["current_turn"],
            "pairs_found": room["pairs_found"],
            "wins": room["wins"],
            "game_over": game_over,
            "match_over": match_over
        }, room=code)

        if game_over and not match_over:
            room["starting_player_index"] = 1 - room["starting_player_index"]
            start_new_game(room)

            emit('memory_new_game', {
                "cards": room["cards"],
                "current_turn": room["current_turn"],
                "pairs_found": room["pairs_found"]
            }, room=code)


    @socketio.on('memory_resolve_mismatch')
    def handle_resolve_mismatch(data):

        if "user_id" not in session:
            return

        code = data.get("code")

        if code not in rooms:
            return

        room = rooms[code]

        if room["closed"]:
            return

        username = session.get("username", "Unknown")

        if username not in room["players"]:
            return

        if len(room["flipped"]) != 2:
            return

        room["flipped"] = []

        room["current_turn"] = _other_player(room, room["current_turn"])

        emit('memory_flip_result', {
            "cards": room["cards"],
            "flipped": room["flipped"],
            "current_turn": room["current_turn"],
            "pairs_found": room["pairs_found"],
            "wins": room["wins"],
            "game_over": False,
            "match_over": False
        }, room=code)


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
            emit('memory_opponent_left', {"winner": winner}, room=code)


    @socketio.on('memory_restart_request')
    def handle_restart_request(data):

        if "user_id" not in session:
            return

        code = data.get("code")

        if code not in rooms:
            emit('memory_join_error', {"error": "Room not found"})
            return

        room = rooms[code]
        username = session.get("username", "Unknown")

        if username not in room["players"]:
            return

        if len(room["players"]) < 2:
            emit('memory_join_error', {"error": "Your opponent left"})
            return

        emit('memory_restart_requested', {"from": username}, room=code, include_self=False)


    @socketio.on('memory_restart_response')
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
            emit('memory_restart_declined', {"by": username}, room=code, include_self=False)
            return

        room["wins"] = {p: 0 for p in room["players"]}
        room["starting_player_index"] = 0
        room["closed"] = False

        start_new_game(room)

        emit('memory_match_ready', {
            "players": room["players"],
            "wins": room["wins"],
            "wins_needed": WINS_NEEDED,
            "cards": room["cards"],
            "current_turn": room["current_turn"]
        }, room=code)