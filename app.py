from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash

from games.rps.logic import rps, reset_game
from games.hangman.logic import new_game, guess_letter, get_display_word
from games.auth.logic import create_user, verify_user
from database import init_db, save_state, load_state

app = Flask(__name__)
app.secret_key = '2502'

init_db()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


@app.route('/')
@login_required
def home():
    return render_template('home.html')


# ---------------- AUTH ----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if create_user(username, password):
            return redirect(url_for("login"))
        flash("Username already taken")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user_id = verify_user(username, password)
        if user_id:
            session["user_id"] = user_id
            session["username"] = username
            return redirect(url_for("home"))
        flash("Invalid credentials")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ---------------- RPS ----------------

@app.route("/rps")
@login_required
def rps_page():
    return render_template("games/rps.html")


@app.route("/api/rps", methods=["POST"])
@login_required
def play_rps():
    data = request.get_json()
    player_choice = data["choice"]
    user_id = session["user_id"]

    state = load_state(user_id, "rps") or {"player_score": 0, "computer_score": 0}
    result = rps(player_choice, state["player_score"], state["computer_score"])

    save_state(user_id, "rps", {
        "player_score": result["player_score"],
        "computer_score": result["computer_score"]
    })

    return jsonify(result)


@app.route("/api/rps/reset", methods=["POST"])
@login_required
def reset_rps():
    result = reset_game()
    save_state(session["user_id"], "rps", result)
    return jsonify(result)


# ---------------- HANGMAN ----------------

@app.route("/hangman")
@login_required
def hangman_page():
    return render_template("games/hangman.html")


@app.route("/api/hangman/new", methods=["POST"])
@login_required
def start_hangman():
    game = new_game()
    save_state(session["user_id"], "hangman", game)

    return jsonify({
        "display_word": get_display_word(game),
        "guessed_letters": game["guessed_letters"],
        "incorrect_guesses": game["incorrect_guesses"],
        "max_incorrect_guesses": game["max_incorrect_guesses"],
        "game_over": False
    })


@app.route("/api/hangman/guess", methods=["POST"])
@login_required
def play_hangman():
    data = request.get_json()
    letter = data["guess"]
    user_id = session["user_id"]

    game = load_state(user_id, "hangman") or new_game()
    game = guess_letter(game, letter)
    save_state(user_id, "hangman", game)

    display_word = get_display_word(game)
    won = "_" not in display_word
    lost = game["incorrect_guesses"] >= game["max_incorrect_guesses"]

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