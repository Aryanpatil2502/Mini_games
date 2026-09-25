import random
import string
from flask import session
from flask_socketio import emit, join_room as socketio_join_room

rooms = {}

VALID_CHOICES = ("rock", "paper", "scissors")


def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))


def register_rps_multiplayer(socketio):

    @socketio.on('rps_create_room')
    def handle_create_room(data=None):

        if "user_id" not in session:
            emit('rps_join_error', {"error": "Not logged in"})
            return

        code = generate_code()

        while code in rooms:
            code = generate_code()

        rooms[code] = {
            "players": [],
            "choices": {}
        }

        emit('rps_room_created', {"code": code})


    @socketio.on('rps_join_room')
    def handle_join_room(data):

        if "user_id" not in session:
            emit('rps_join_error', {"error": "Not logged in"})
            return

        code = str(data.get("code", "")).strip().upper()

        if code not in rooms:
            emit('rps_join_error', {"error": "Room not found"})
            return

        room = rooms[code]
        username = session.get("username", "Unknown")

        # Player is already in this room (e.g. page refresh) - let them back in
        if username in room["players"]:
            socketio_join_room(code)
            emit('rps_joined', {"code": code})

            if len(room["players"]) == 2:
                emit('rps_match_ready', {"players": room["players"]})
            return

        if len(room["players"]) >= 2:
            emit('rps_join_error', {"error": "Room is full"})
            return

        room["players"].append(username)
        socketio_join_room(code)

        emit('rps_joined', {"code": code})

        if len(room["players"]) == 2:
            emit('rps_match_ready', {"players": room["players"]}, room=code)


    @socketio.on('rps_choice_made')
    def handle_choice_made(data):

        if "user_id" not in session:
            return

        code = data.get("code")
        choice = data.get("choice")

        if code not in rooms or choice not in VALID_CHOICES:
            return

        room = rooms[code]
        username = session.get("username", "Unknown")

        # Need two players, and the sender must be one of them
        if len(room["players"]) < 2 or username not in room["players"]:
            return

        room["choices"][username] = choice

        player1 = room["players"][0]
        player2 = room["players"][1]

        choice1 = room["choices"].get(player1)
        choice2 = room["choices"].get(player2)

        if choice1 is None or choice2 is None:
            return

        if choice1 == choice2:
            result = "It's a tie!"
            winner = None

        elif (
            (choice1 == "rock" and choice2 == "scissors")
            or (choice1 == "paper" and choice2 == "rock")
            or (choice1 == "scissors" and choice2 == "paper")
        ):
            result = f"{player1} wins!"
            winner = player1

        else:
            result = f"{player2} wins!"
            winner = player2

        emit('rps_round_result', {
            "player_1": player1,
            "choice_1": choice1,
            "player_2": player2,
            "choice_2": choice2,
            "result": result,
            "winner": winner
        }, room=code)

        room["choices"] = {}