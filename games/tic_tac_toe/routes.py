import json
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for

from .logic import new_tictactoe_game, make_move, computer_move, check_winner

from database import (
    get_tictactoe_game,
    create_tictactoe_game,
    update_tictactoe_game
)

tictactoe_bp = Blueprint("tictactoe", __name__)


@tictactoe_bp.route("/tictactoe")
def tictactoe_page():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("games/tictactoe.html")


@tictactoe_bp.route("/api/tictactoe/current", methods=["GET"])
def current_tictactoe():

    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["user_id"]

    db_game = get_tictactoe_game(user_id)

    if db_game is None:
        return jsonify({
            "game_exists": False
        })

    return jsonify({
        "game_exists": True,
        "board": json.loads(db_game["board"]),
        "current_player": db_game["current_player"],
        "winner": db_game["winner"],
        "status": db_game["status"]
    })


@tictactoe_bp.route("/api/tictactoe/new", methods=["POST"])
def start_tictactoe():

    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["user_id"]

    game = new_tictactoe_game()

    existing_game = get_tictactoe_game(user_id)

    if existing_game is None:
        create_tictactoe_game(
            user_id,
            game["board"],
            game["current_player"]
        )
    else:
        update_tictactoe_game(
            user_id,
            game["board"],
            game["current_player"],
            game["winner"],
            "playing"
        )

    return jsonify({
        "board": game["board"],
        "current_player": game["current_player"],
        "winner": game["winner"],
        "status": "playing"
    })


@tictactoe_bp.route("/api/tictactoe/move", methods=["POST"])
def play_tictactoe():

    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["user_id"]

    data = request.get_json()
    move = data["move"]

    db_game = get_tictactoe_game(user_id)

    if db_game is None:
        return jsonify({"error": "No game found"}), 400

    game = {
        "board": json.loads(db_game["board"]),
        "current_player": db_game["current_player"],
        "winner": db_game["winner"],
        "game_over": db_game["status"] != "playing"
    }

    game, success = make_move(game, move)

    if not success:
        return jsonify({"error": "Invalid move"}), 400

    game = check_winner(game)

    if not game["game_over"]:
        game = computer_move(game)
        game = check_winner(game)

    if game["winner"]:
        status = "won" if game["winner"] == "X" else "lost"
    elif game["game_over"]:
        status = "draw"
    else:
        status = "playing"

    update_tictactoe_game(
        user_id,
        game["board"],
        game["current_player"],
        game["winner"],
        status
    )

    return jsonify({
        "board": game["board"],
        "current_player": game["current_player"],
        "winner": game["winner"],
        "status": status
    })