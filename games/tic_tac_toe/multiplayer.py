import random
import string
from flask import session, request
from flask_socketio import emit, join_room as socketio_join_room

from .logic import new_tictactoe_game, make_move, check_winner

rooms = {}
sid_to_room = {}  #

WINS_NEEDED = 5


def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))


def start_new_game(room):
    game = new_tictactoe_game()

    room["board"] = game["board"]
    room["winner"] = game["winner"]
    room["game_over"] = game["game_over"]
    room["current_turn"] = room["players"][room["starting_player_index"]]


def _other_player(room, username):
    for p in room["players"]:
        if p != username:
            return p
    return None


def _symbols(room):
   
    starter = room["players"][room["starting_player_index"]]
    other = _other_player(room, starter)
    return {starter: "X", other: "O"}


def _match_ready_payload(room):
    return {
        "players": room["players"],
        "wins": room["wins"],
        "wins_needed": WINS_NEEDED,
        "board": room["board"],
        "current_turn": room["current_turn"],
        "symbols": _symbols(room)
    }


def _finish_game(room):

    winner_username = None

    if room["winner"] is not None:
        for username, symbol in _symbols(room).items():
            if symbol == room["winner"]:
                winner_username = username

        room["wins"][winner_username] += 1

    match_over = max(room["wins"].values()) >= WINS_NEEDED

    if match_over:
        room["closed"] = True

    return winner_username, match_over


def register_tictactoe_multiplayer(socketio):

    @socketio.on('ttt_create_room')
    def handle_create_room(data=None):

        if "user_id" not in session:
            emit('ttt_join_error', {"error": "Not logged in"})
            return

        code = generate_code()

        while code in rooms:
            code = generate_code()

        rooms[code] = {
            "players": [],
            "board": [],
            "current_turn": None,
            "winner": None,
            "game_over": False,
            "wins": {},
            "starting_player_index": 0,
            "closed": False,
            "abandoned": False,     
            "restart_from": None      
        }

        emit('ttt_room_created', {"code": code})


    @socketio.on('ttt_join_room')
    def handle_join_room(data):

        if "user_id" not in session:
            emit('ttt_join_error', {"error": "Not logged in"})
            return

        code = str(data.get("code", "")).strip().upper()

        if code not in rooms:
            emit('ttt_join_error', {"error": "Room not found"})
            return

        room = rooms[code]

        if room["closed"]:
            emit('ttt_join_error', {"error": "This room has ended"})
            return

        username = session.get("username", "Unknown")

        if username in room["players"]:
            socketio_join_room(code)
            sid_to_room[request.sid] = code

            emit('ttt_joined', {"code": code})

            if len(room["players"]) == 2:
                emit('ttt_match_ready', _match_ready_payload(room))
            return

        if len(room["players"]) >= 2:
            emit('ttt_join_error', {"error": "Room is full"})
            return

        room["players"].append(username)
        room["wins"][username] = 0

        socketio_join_room(code)
        sid_to_room[request.sid] = code

        emit('ttt_joined', {"code": code})

        if len(room["players"]) == 2:

            start_new_game(room)

            emit('ttt_match_ready', _match_ready_payload(room), room=code)


    @socketio.on('ttt_move')
    def handle_move(data):

        if "user_id" not in session:
            return

        code = data.get("code")
        move = data.get("move")

        if code not in rooms:
            return

        if not isinstance(move, int) or isinstance(move, bool) or not 0 <= move <= 8:
            return

        room = rooms[code]

        if room["closed"]:
            return

        username = session.get("username", "Unknown")

        if len(room["players"]) < 2 or username not in room["players"]:
            return

        if room["current_turn"] != username:
            return

        my_symbol = _symbols(room)[username]

        game = {
            "board": room["board"],
            "current_player": my_symbol,
            "winner": room["winner"],
            "game_over": room["game_over"]
        }

        game, success = make_move(game, move)

        if not success:
            return

        game = check_winner(game)

        room["board"] = game["board"]
        room["winner"] = game["winner"]
        room["game_over"] = game["game_over"]

        game_over = room["game_over"]
        match_over = False
        winner_username = None

        if game_over:
            winner_username, match_over = _finish_game(room)
        else:
            room["current_turn"] = _other_player(room, username)

        result = {
            "board": [row[:] for row in room["board"]],
            "winner": room["winner"],              
            "winner_username": winner_username,
            "current_turn": room["current_turn"],
            "wins": room["wins"],
            "symbols": _symbols(room),
            "game_over": game_over,
            "match_over": match_over
        }

        emit('ttt_move_result', result, room=code)

        if game_over and not match_over:
            room["starting_player_index"] = 1 - room["starting_player_index"]
            start_new_game(room)

            emit('ttt_new_game', {
                "board": room["board"],
                "current_turn": room["current_turn"],
                "symbols": _symbols(room)
            }, room=code)


    @socketio.on('disconnect')
    def handle_disconnect():

        code = sid_to_room.pop(request.sid, None)

        if code is None or code not in rooms:
            return

        room = rooms[code]

        username = session.get("username", "Unknown")

        if username not in room["players"]:
            return

        already_closed = room["closed"]

        room["closed"] = True
        room["abandoned"] = True
        room["restart_from"] = None

        if already_closed:
            return

        remaining = [p for p in room["players"] if p != username]

        if remaining:
            winner = remaining[0]
            emit('ttt_opponent_left', {"winner": winner}, room=code)


    @socketio.on('ttt_restart_request')
    def handle_restart_request(data):

        if "user_id" not in session:
            return

        code = data.get("code")

        if code not in rooms:
            emit('ttt_join_error', {"error": "Room not found"})
            return

        room = rooms[code]
        username = session.get("username", "Unknown")

        if username not in room["players"]:
            return

        if len(room["players"]) < 2 or room["abandoned"]:
            emit('ttt_join_error', {"error": "Your opponent left"})
            return

        room["restart_from"] = username

        emit('ttt_restart_requested', {"from": username}, room=code, include_self=False)


    @socketio.on('ttt_restart_response')
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

        if room["restart_from"] is None or room["restart_from"] == username:
            return

        if room["abandoned"]:
            return

        room["restart_from"] = None

        if not accepted:
            emit('ttt_restart_declined', {"by": username}, room=code, include_self=False)
            return

        room["wins"] = {p: 0 for p in room["players"]}
        room["starting_player_index"] = 0
        room["closed"] = False

        start_new_game(room)

        emit('ttt_match_ready', _match_ready_payload(room), room=code)