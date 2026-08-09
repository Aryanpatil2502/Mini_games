import random


words = [
    "apple",
    "banana",
    "orange",
    "guitar",
    "piano",
    "rocket",
    "planet",
    "castle",
    "forest",
    "mountain",
    "river",
    "ocean",
    "island",
    "bridge",
    "school",
    "college",
    "teacher",
    "student",
    "computer",
    "keyboard",
    "internet",
    "program",
    "python",
    "javascript",
    "developer",
    "database",
    "algorithm",
    "function",
    "variable",
    "software",
    "hardware",
    "football",
    "cricket",
    "basketball",
    "player",
    "champion",
    "elephant",
    "tiger",
    "lion",
    "giraffe",
    "monkey",
    "penguin",
    "dolphin",
    "rabbit",
    "camera",
    "bicycle",
    "airplane",
    "submarine",
    "hospital",
    "library"
]


def new_game():

    word = random.choice(words)

    return {
        "word": word,
        "guessed_letters": [],
        "incorrect_guesses": 0,
        "max_incorrect_guesses": 6
    }


def guess_letter(game, letter):


    if game["incorrect_guesses"] >= game["max_incorrect_guesses"]:
        return game

    if all(letter in game["guessed_letters"] for letter in game["word"]):
        return game

    if letter in game["guessed_letters"]:
        return game

    game["guessed_letters"].append(letter)

    if letter not in game["word"]:
        game["incorrect_guesses"] += 1

    return game


def get_display_word(game):

    display_word = ""

    for letter in game["word"]:

        if letter in game["guessed_letters"]:
            display_word += letter

        else:
            display_word += "_"

    return display_word