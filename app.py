from flask import Flask,render_template,request, jsonify, session, redirect, url_for
from games.rps.logic import rps, reset_game
from games.hangman.logic import new_game, guess_letter, get_display_word
from werkzeug.security import generate_password_hash, check_password_hash
from database import (
    init_db,
    add_user,
    get_user,
    delete_user,
    # RPS
    get_rps_game,
    create_rps_game,
    update_rps_score,

    # Hangman
    get_hangman_game,
    create_hangman_game,
    update_hangman_game
)
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")  

init_db()

@app.route('/')
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template('home.html')

@app.route("/rps")
def rps_page():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("games/rps.html")

@app.route("/hangman")
def hangman_page():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("games/hangman.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("auth/register.html")

    username = request.form["username"]
    password = request.form["password"]

    existing_user = get_user(username)

    if existing_user:
        return "Username already exists"

    password_hash = generate_password_hash(password)

    add_user(username, password_hash)

    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("auth/login.html")

    username = request.form["username"]
    password = request.form["password"]

    user = get_user(username)

    if user is None:
        return redirect(url_for("register"))

    if not check_password_hash(
        user["password_hash"],
        password
    ):
        return "Invalid username or password"

    session["user_id"] = user["id"]
    session["username"] = user["username"]

    return redirect(url_for("home"))

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))

@app.route("/delete-account", methods=["POST"])
def delete_account():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    delete_user(user_id)

    session.clear()

    return redirect(url_for("register"))

# RPS

@app.route("/api/rps", methods=["POST"])
def play_rps():

    data = request.get_json()
    player_choice = data["choice"]

    # Get current logged-in user
    user_id = session["user_id"]

    # Get this user's RPS game
    game = get_rps_game(user_id)

    # If user doesn't have an RPS game yet, create one
    if game is None:
        create_rps_game(user_id)
        game = get_rps_game(user_id)

    # Get scores from database
    player_score = game["player_score"]
    computer_score = game["computer_score"]

    # Play the game
    result = rps(
        player_choice,
        player_score,
        computer_score
    )

    # Save new scores to database
    update_rps_score(
        user_id,
        result["player_score"],
        result["computer_score"]
    )

    return jsonify(result)


@app.route("/api/rps/reset", methods=["POST"])
def reset_rps():
    result = reset_game()
    session["player_score"] = result["player_score"]
    session["computer_score"] = result["computer_score"]

    return jsonify(result)

# HANGMAN

@app.route("/api/hangman/current", methods=["GET"])
def current_hangman():

    user_id = session["user_id"]

    game = get_hangman_game(user_id)

    # User has never played Hangman
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

@app.route("/api/hangman/new", methods=["POST"])
def start_hangman():

    user_id = session["user_id"]

    # Create a new game using your existing logic
    game = new_game()

    # Save it to database
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



@app.route("/api/hangman/guess", methods=["POST"])
def play_hangman():

    user_id = session["user_id"]

    data = request.get_json()
    letter = data["guess"]

    # Get this user's Hangman game from database
    db_game = get_hangman_game(user_id)

    if db_game is None:
        return jsonify({
            "error": "No game found"
        }), 400

    # Convert database row back into the format
    # your existing game logic expects
    game = {
        "word": db_game["word"],
        "guessed_letters": list(db_game["guessed_letters"]),
        "incorrect_guesses": db_game["incorrect_guesses"],
        "max_incorrect_guesses": db_game["max_incorrect_guesses"]
    }

    # Use your existing logic
    game = guess_letter(game, letter)

    display_word = get_display_word(game)

    won = "_" not in display_word

    lost = (
        game["incorrect_guesses"]
        >= game["max_incorrect_guesses"]
    )

    # Determine status for database
    if won:
        status = "won"
    elif lost:
        status = "lost"
    else:
        status = "playing"

    # Save updated game
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
if __name__ == '__main__':
    app.run(debug=True)

