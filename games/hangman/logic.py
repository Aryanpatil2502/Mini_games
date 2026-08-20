import random


    # List of words to choose from
words = [
    "apple","banana","orange","guitar","piano",
    "rocket","planet","castle","forest","mountain","river","ocean","island","bridge","school",
    "college","teacher","student","computer","keyboard","internet","program","python",
    "javascript","developer","database",
    "algorithm","function","variable","software","hardware","football","cricket","basketball",
    "player","champion","elephant","tiger",
    "lion","giraffe","monkey","penguin","dolphin","rabbit","camera","bicycle","airplane",
    "submarine","hospital", "library"
]

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