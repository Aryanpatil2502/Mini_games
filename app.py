import json
from flask import Flask,render_template,request, jsonify, session, redirect, url_for
from games.rps.logic import rps, reset_game
from games.hangman.logic import new_hangman_game, guess_letter, get_display_word
from werkzeug.security import generate_password_hash, check_password_hash
from games.tic_tac_toe.logic import new_tictactoe_game, make_move, computer_move, check_winner
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
    update_hangman_game,

    # Tic Tac Toe
    get_tictactoe_game,
    create_tictactoe_game,
    update_tictactoe_game
)
from games.rps import rps_bp
from games.hangman import hangman_bp
from games.tic_tac_toe import tictactoe_bp


app = Flask(__name__)
app.register_blueprint(rps_bp)
app.register_blueprint(hangman_bp)
app.register_blueprint(tictactoe_bp)


import os
from dotenv import load_dotenv
load_dotenv()

app.secret_key = os.environ.get("SECRET_KEY")  

init_db()

@app.route('/')
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template('home.html')


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("auth/register.html")

    username = request.form["username"]
    password = request.form["password"]
    confirm_password = request.form["confirm_password"]

    if password != confirm_password:
        return render_template(
            "auth/register.html",
            error="Passwords do not match"
        )
 

    existing_user = get_user(username)

    if existing_user:
        return redirect(url_for("register"))

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


# HANGMAN


# Tic Tac Toe



if __name__ == '__main__':
    app.run(debug=True)

