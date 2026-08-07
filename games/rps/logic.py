import random


def rps(player_choice, player_score, computer_score):

    choices = ["rock", "paper", "scissors"]
    computer_choice = random.choice(choices)

    if player_choice == computer_choice:
        result = "It's a tie!"

    elif (
        (player_choice == "rock" and computer_choice == "scissors")
        or (player_choice == "paper" and computer_choice == "rock")
        or (player_choice == "scissors" and computer_choice == "paper")
    ):
        result = "You win!"
        player_score += 1

    else:
        result = "Computer wins!"
        computer_score += 1

    return {
        "player": player_choice,
        "computer": computer_choice,
        "result": result,
        "player_score": player_score,
        "computer_score": computer_score
    }