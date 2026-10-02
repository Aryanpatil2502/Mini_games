# Mini Games

A real-time mini games app built with Flask, Flask-SocketIO, SQLite, HTML, CSS, and JavaScript.

---

# Prerequisites

You can run this project in two ways.

## Option 1: Docker

You need:

* Git
* Docker
* Docker Compose

## Option 2: uv

You need:

* Git
* Python
* uv


---

# Environment Variables

Before running the application using either method, create a `.env` file in the root directory of the project.

Your project should contain:

```text
Mini_games/
├── .env
├── Dockerfile
├── compose.yaml
├── pyproject.toml
├── uv.lock
├── app.py
└── ...
```

Add your secret key to `.env`:

```env
SECRET_KEY="your-secret-key-here"
```

Replace `your-secret-key-here` with your own secret key.

---

# Running with Docker

## 1. Clone the repository

```bash
git clone https://github.com/Aryanpatil2502/Mini_games
cd Mini_games
```

## 2. Start the application

```bash
docker compose up --build
```


## 3. Stop the application

```bash
docker compose down
```

---

# Running with uv

## 1. Clone the repository

```bash
git clone https://github.com/Aryanpatil2502/Mini_games
cd Mini_games
```

## 2. Install dependencies

```bash
uv sync
```

## 3. Start the application

```bash
uv run app.py
```

---

# SQLite Database

This application uses SQLite. The database is stored in the `data/` folder as `user.db`.

You do not need to manually create the database. The application will initialize it when required.

When running with Docker, the `data/` folder is mounted as a volume, so your accounts and saved games are kept between rebuilds. Do not delete this folder if you want to preserve your data.

---
