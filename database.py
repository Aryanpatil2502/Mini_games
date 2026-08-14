import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / "users.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
""")

    conn.execute("""
    CREATE TABLE IF NOT EXISTS game_state (
        user_id INTEGER NOT NULL,
        game_name TEXT NOT NULL,
        state TEXT NOT NULL,
        PRIMARY KEY (user_id, game_name),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")

    conn.commit()
    conn.close()

def save_state(user_id, game_name, state: dict):
    conn = get_db()
    conn.execute("""
        INSERT INTO game_state (user_id, game_name, state)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, game_name)
        DO UPDATE SET state = excluded.state
    """, (user_id, game_name, json.dumps(state)))
    conn.commit()
    conn.close()


def load_state(user_id, game_name):
    conn = get_db()
    row = conn.execute(
        "SELECT state FROM game_state WHERE user_id = ? AND game_name = ?",
        (user_id, game_name)
    ).fetchone()
    conn.close()
    return json.loads(row["state"]) if row else None