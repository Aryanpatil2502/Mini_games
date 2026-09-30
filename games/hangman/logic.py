import random
import os

WORDS_FILE = os.path.join(os.path.dirname(__file__), "words.txt")


def load_words():
    with open(WORDS_FILE) as f:
        return [line.strip().lower() for line in f if line.strip()]

words = load_words()

def new_hangman_game():

    word_to_guess = random.choice(words)

    return {
        "word": word_to_guess,
        "guessed_letters": [],
        "incorrect_guesses": 0,
        "max_incorrect_guesses": 6
    }

def guess_letter(game, guess):

    word = game["word"]
    guessed_letters = game["guessed_letters"]

    if guess in guessed_letters:
        return game

    guessed_letters.append(guess)

    if guess not in word:
        game["incorrect_guesses"] += 1

    return game

def get_display_word(game):

    word = game["word"]
    guessed_letters = game["guessed_letters"]

    return "".join(
        letter if letter in guessed_letters else "_"
        for letter in word
    )