from flask import Flask,render_template,request, jsonify, session
from games.rps.logic import rps, reset_game
from games.hangman.logic import new_game, guess_letter, get_display_word

app = Flask(__name__)
app.secret_key = '2502'  

@app.route('/')
def home():
    return render_template('home.html')

@app.route("/rps")
def rps_page():
    return render_template("games/rps.html")

@app.route("/hangman")
def hangman_page():
    return render_template("games/hangman.html")



@app.route("/api/rps", methods=["POST"])
def play_rps():

    data = request.get_json()
    player_choice = data["choice"]

    player_score = session.get("player_score", 0)
    computer_score = session.get("computer_score", 0)

    result = rps(player_choice, player_score, computer_score)

    session["player_score"] = result["player_score"]
    session["computer_score"] = result["computer_score"]

    return jsonify(result)


@app.route("/api/rps/reset", methods=["POST"])
def reset_rps():
    result = reset_game()
    session["player_score"] = result["player_score"]
    session["computer_score"] = result["computer_score"]

    return jsonify(result)

# ---------------- HANGMAN ----------------

@app.route("/api/hangman/new", methods=["POST"])
def start_hangman():

    game = new_game()

    session["hangman"] = game

    return jsonify({
        "display_word": get_display_word(game),
        "guessed_letters": game["guessed_letters"],
        "incorrect_guesses": game["incorrect_guesses"],
        "max_incorrect_guesses": game["max_incorrect_guesses"],
        "game_over": False
    })


@app.route("/api/hangman/guess", methods=["POST"])
def play_hangman():

    data = request.get_json()

    letter = data["guess"]

    game = session.get("hangman")

    if game is None:
        game = new_game()

    game = guess_letter(game, letter)

    session["hangman"] = game

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

