import random
import string
from flask import session, request
from flask_socketio import emit, join_room as socketio_join_room

rooms = {}
sid_to_room = {}  

VALID_CHOICES = ("rock", "paper", "scissors")
WINS_NEEDED = 5


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
            "choices": {},
            "wins": {},
            "closed": False
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

        
        if room["closed"]:
            emit('rps_join_error', {"error": "This room has ended"})
            return

        username = session.get("username", "Unknown")

    
        if username in room["players"]:
            socketio_join_room(code)
            sid_to_room[request.sid] = code

            emit('rps_joined', {"code": code})

            if len(room["players"]) == 2:
                emit('rps_match_ready', {
                    "players": room["players"],
                    "wins": room["wins"],
                    "wins_needed": WINS_NEEDED
                })
            return

        if len(room["players"]) >= 2:
            emit('rps_join_error', {"error": "Room is full"})
            return

        room["players"].append(username)
        room["wins"][username] = 0

        socketio_join_room(code)
        sid_to_room[request.sid] = code

        emit('rps_joined', {"code": code})

        if len(room["players"]) == 2:
            emit('rps_match_ready', {
                "players": room["players"],
                "wins": room["wins"],
                "wins_needed": WINS_NEEDED
            }, room=code)


    @socketio.on('rps_choice_made')
    def handle_choice_made(data):

        if "user_id" not in session:
            return

        code = data.get("code")
        choice = data.get("choice")

        if code not in rooms or choice not in VALID_CHOICES:
            return

        room = rooms[code]

        if room["closed"]:
            return

        username = session.get("username", "Unknown")

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

        if winner is not None:
            room["wins"][winner] += 1

        match_over = winner is not None and room["wins"][winner] >= WINS_NEEDED

        if match_over:
            room["closed"] = True

        emit('rps_round_result', {
            "player_1": player1,
            "choice_1": choice1,
            "player_2": player2,
            "choice_2": choice2,
            "result": result,
            "winner": winner,
            "wins": room["wins"],
            "match_over": match_over
        }, room=code)

        room["choices"] = {}


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
            emit('rps_opponent_left', {"winner": winner}, room=code)



    @socketio.on('rps_restart_request')
    def handle_restart_request(data):

        if "user_id" not in session:
            return

        code = data.get("code")

        if code not in rooms:
            emit('rps_join_error', {"error": "Room not found"})
            return

        room = rooms[code]
        username = session.get("username", "Unknown")

        if username not in room["players"]:
            return

        if len(room["players"]) < 2:
            emit('rps_join_error', {"error": "Your opponent left"})
            return

        emit('rps_restart_requested', {"from": username}, room=code, include_self=False)


    @socketio.on('rps_restart_response')
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
            emit('rps_restart_declined', {"by": username}, room=code, include_self=False)
            return

        room["choices"] = {}
        room["wins"] = {p: 0 for p in room["players"]}
        room["closed"] = False

        emit('rps_match_ready', {
            "players": room["players"],
            "wins": room["wins"],
            "wins_needed": WINS_NEEDED
        }, room=code)