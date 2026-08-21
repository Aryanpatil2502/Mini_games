from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for

from .logic import new_hangman_game, guess_letter, get_display_word

from database import (
    get_hangman_game,
    create_hangman_game,
    update_hangman_game
)

hangman_bp = Blueprint("hangman", __name__)


@hangman_bp.route("/hangman")
def hangman_page():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("games/hangman.html")


@hangman_bp.route("/api/hangman/current", methods=["GET"])
def current_hangman():

    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["user_id"]

    game = get_hangman_game(user_id)

    if game is None:
        return jsonify({
            "game_exists": False
        })

    guessed_letters = list(game["guessed_letters"])

    game_data = {
        "word": game["word"],
        "guessed_letters": guessed_letters,
        "incorrect_guesses": game["incorrect_guesses"],
        "max_incorrect_guesses": game["max_incorrect_guesses"]
    }

    display_word = get_display_word(game_data)

    won = "_" not in display_word
    lost = game["incorrect_guesses"] >= game["max_incorrect_guesses"]

    return jsonify({
        "game_exists": True,
        "display_word": display_word,
        "guessed_letters": guessed_letters,
        "incorrect_guesses": game["incorrect_guesses"],
        "max_incorrect_guesses": game["max_incorrect_guesses"],
        "won": won,
        "lost": lost,
        "word": game["word"] if lost else ""
    })


@hangman_bp.route("/api/hangman/new", methods=["POST"])
def start_hangman():

    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["user_id"]

    game = new_hangman_game()

    existing_game = get_hangman_game(user_id)

    if existing_game is None:
        create_hangman_game(
            user_id,
            game["word"],
            "",
            0
        )
    else:
        update_hangman_game(
            user_id,
            game["word"],
            "",
            0,
            "playing"
        )

    return jsonify({
        "display_word": get_display_word(game),
        "guessed_letters": game["guessed_letters"],
        "incorrect_guesses": game["incorrect_guesses"],
        "max_incorrect_guesses": game["max_incorrect_guesses"],
        "game_over": False
    })


@hangman_bp.route("/api/hangman/guess", methods=["POST"])
def play_hangman():

    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["user_id"]

    data = request.get_json()
    letter = data["guess"]

    db_game = get_hangman_game(user_id)

    if db_game is None:
        return jsonify({
            "error": "No game found"
        }), 400

    game = {
        "word": db_game["word"],
        "guessed_letters": list(db_game["guessed_letters"]),
        "incorrect_guesses": db_game["incorrect_guesses"],
        "max_incorrect_guesses": db_game["max_incorrect_guesses"]
    }

    game = guess_letter(game, letter)

    display_word = get_display_word(game)

    won = "_" not in display_word

    lost = (
        game["incorrect_guesses"]
        >= game["max_incorrect_guesses"]
    )

    if won:
        status = "won"
    elif lost:
        status = "lost"
    else:
        status = "playing"

    update_hangman_game(
        user_id,
        game["word"],
        "".join(game["guessed_letters"]),
        game["incorrect_guesses"],
        status
    )

    return jsonify({
        "display_word": display_word,
        "guessed_letters": game["guessed_letters"],
        "incorrect_guesses": game["incorrect_guesses"],
        "max_incorrect_guesses": game["max_incorrect_guesses"],
        "won": won,
        "lost": lost,
        "word": game["word"]
    })