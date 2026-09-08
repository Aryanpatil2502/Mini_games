import json
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for

from .logic import new_memory_game, play, resolve_mismatch

from database import (
    get_memory_game,
    create_memory_game,
    update_memory_game
)

memory_bp = Blueprint("memory", __name__)


def _game_to_dict(db_game):
    return {
        "cards": json.loads(db_game["cards"]),
        "flipped": json.loads(db_game["flipped"]),
        "matched_count": db_game["matched_count"],
        "game_over": bool(db_game["game_over"])
    }


def _save_game(user_id, game, is_new):
    if is_new:
        create_memory_game(
            user_id,
            game["cards"],
            game["flipped"],
            game["matched_count"],
            game["game_over"]
        )
    else:
        update_memory_game(
            user_id,
            game["cards"],
            game["flipped"],
            game["matched_count"],
            game["game_over"]
        )


@memory_bp.route("/memory")
def memory_page():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("games/memory.html")


@memory_bp.route("/api/memory/current", methods=["GET"])
def current_memory():

    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["user_id"]

    db_game = get_memory_game(user_id)

    if db_game is None:
        return jsonify({"game_exists": False})

    game = _game_to_dict(db_game)
    game["game_exists"] = True

    return jsonify(game)


@memory_bp.route("/api/memory/new", methods=["POST"])
def new_memory():

    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["user_id"]

    game = new_memory_game()

    existing_game = get_memory_game(user_id)

    _save_game(user_id, game, is_new=(existing_game is None))

    game["game_exists"] = True

    return jsonify(game)


@memory_bp.route("/api/memory/play", methods=["POST"])
def play_memory():

    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["user_id"]

    data = request.get_json()
    index = data["index"]

    db_game = get_memory_game(user_id)

    if db_game is None:
        return jsonify({"error": "No game found"}), 400

    game = _game_to_dict(db_game)

    game = play(game, index)

    _save_game(user_id, game, is_new=False)

    return jsonify(game)

@memory_bp.route("/api/memory/resolve", methods=["POST"])
def resolve_memory():

    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["user_id"]

    db_game = get_memory_game(user_id)

    if db_game is None:
        return jsonify({"error": "No game found"}), 400

    game = _game_to_dict(db_game)

    game = resolve_mismatch(game)

    _save_game(user_id, game, is_new=False)

    return jsonify(game)