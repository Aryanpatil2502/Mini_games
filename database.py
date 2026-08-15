import sqlite3


DB_PATH = "user.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db()

    # Users table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    # RPS game state
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rps_games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            player_score INTEGER DEFAULT 0,
            computer_score INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Hangman game state
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hangman_games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            word TEXT NOT NULL,
            guessed_letters TEXT DEFAULT '',
            incorrect_guesses INTEGER DEFAULT 0,
            max_incorrect_guesses INTEGER DEFAULT 6,
            status TEXT DEFAULT 'playing',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()

# USERS

def add_user(username, password_hash):
    conn = get_db()
    conn.execute(
        """
        INSERT INTO users (username, password_hash)
        VALUES (?, ?)
        """,
        (username, password_hash)
    )
    conn.commit()
    conn.close()

def get_user(username):

    conn = get_db()

    user = conn.execute(
        """
        SELECT * FROM users
        WHERE username = ?
        """,
        (username,)
    ).fetchone()

    conn.close()

    return user

def delete_user(user_id):

    conn = get_db()

    # Delete the user's game data first
    conn.execute(
        "DELETE FROM rps_games WHERE user_id = ?",
        (user_id,)
    )

    conn.execute(
        "DELETE FROM hangman_games WHERE user_id = ?",
        (user_id,)
    )

    # Delete the user
    conn.execute(
        "DELETE FROM users WHERE id = ?",
        (user_id,)
    )

    conn.commit()
    conn.close()

# RPS
def get_rps_game(user_id):

    conn = get_db()

    game = conn.execute(
        """
        SELECT * FROM rps_games
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()

    conn.close()

    return game


def create_rps_game(user_id):

    conn = get_db()

    conn.execute(
        """
        INSERT INTO rps_games
        (user_id, player_score, computer_score)
        VALUES (?, 0, 0)
        """,
        (user_id,)
    )

    conn.commit()
    conn.close()


def update_rps_score(user_id, player_score, computer_score):

    conn = get_db()

    conn.execute(
        """
        UPDATE rps_games
        SET player_score = ?, computer_score = ?
        WHERE user_id = ?
        """,
        (player_score, computer_score, user_id)
    )

    conn.commit()
    conn.close()

# Hangman
def get_hangman_game(user_id):

    conn = get_db()

    game = conn.execute(
        """
        SELECT * FROM hangman_games
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()

    conn.close()

    return game


def create_hangman_game(
    user_id,
    word,
    guessed_letters="",
    incorrect_guesses=0
):

    conn = get_db()

    conn.execute(
        """
        INSERT INTO hangman_games
        (
            user_id,
            word,
            guessed_letters,
            incorrect_guesses
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            word,
            guessed_letters,
            incorrect_guesses
        )
    )

    conn.commit()
    conn.close()


def update_hangman_game(
    user_id,
    word,
    guessed_letters,
    incorrect_guesses,
    status
):

    conn = get_db()

    conn.execute(
        """
        UPDATE hangman_games
        SET
            word = ?,
            guessed_letters = ?,
            incorrect_guesses = ?,
            status = ?
        WHERE user_id = ?
        """,
        (
            word,
            guessed_letters,
            incorrect_guesses,
            status,
            user_id
        )
    )

    conn.commit()
    conn.close()