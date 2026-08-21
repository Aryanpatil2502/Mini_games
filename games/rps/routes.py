from flask import Blueprint, render_template, request, jsonify, session

from .logic import rps

from database import (
    get_rps_game,
    create_rps_game,
    update_rps_score
)

rps_bp = Blueprint("rps",__name__)

@rps_bp.route("/rps")
def rps_page():

    user_id = session["user_id"]

    game = get_rps_game(user_id)

    if game is None:
        create_rps_game(user_id)

        game = get_rps_game(user_id)

    return render_template(
        "games/rps.html",
        player_score = game["player_score"],
        computer_score = game["computer_score"]

    )

@rps_bp.route("/api/rps", methods = ["POST"])
def play_rps():

    user_id = session["user_id"]
    data = request.get_json()
    player_choice = data["choice"]

    game = get_rps_game(user_id)

    if game is None:
        create_rps_game(user_id)
        game = get_rps_game(user_id)

    player_score = game["player_score"]
    computer_score = game["computer_score"]

    result = rps(
        player_choice,
        player_score,
        computer_score
    )

    update_rps_score(
        user_id,
        result["player_score"],
        result["computer_score"]
    )

    return jsonify(result)

@rps_bp.route("/api/rps/reset", methods=["POST"])
def reset_rps():

    user_id = session["user_id"]

    update_rps_score(user_id, 0, 0)

    return jsonify({
        "player_score": 0,
        "computer_score": 0
    })
