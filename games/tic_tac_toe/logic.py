import random

def new_tictactoe_game():
    return {
        "board" : [
            ["", "", ""],
            ["", "", ""],
            ["", "", ""]
        ],
        "current_player" : "X",
        "winner" : None,
        "game_over" : False
    }

def make_move(game,move):
    row = move // 3
    col = move % 3

    if game["board"][row][col] != "":
        return game, False

    game["board"][row][col] = game["current_player"]

    if game["current_player"] == "X":
        game["current_player"] = "O"
    else:
        game["current_player"] = "X"

    return game, True


def computer_move(game):
    empty = []
    for i in range(len(game["board"])):
        for j in range(len(game["board"][i])):
            if game["board"][i][j] == "":
                empty.append((i, j))

    if not empty:
        return game

    row, col = random.choice(empty)
    game["board"][row][col] = game["current_player"]

    if game["current_player"] == "X":
        game["current_player"] = "O"
    else:
        game["current_player"] = "X"

    return game

def check_winner(game):
    board = game["board"]

    # Check rows and columns
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] != "":
            game["winner"] = board[i][0]
            game["game_over"] = True
            return game
        if board[0][i] == board[1][i] == board[2][i] != "":
            game["winner"] = board[0][i]
            game["game_over"] = True
            return game

    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] != "":
        game["winner"] = board[0][0]
        game["game_over"] = True
        return game
    if board[0][2] == board[1][1] == board[2][0] != "":
        game["winner"] = board[0][2]
        game["game_over"] = True
        return game

    # Check for draw
    if all(cell != "" for row in board for cell in row):
        game["game_over"] = True

    return game