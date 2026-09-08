import random

def new_memory_game():
    values = [0,1,2,3,4,5,6,7,0,1,2,3,4,5,6,7]     
    random.shuffle(values)

    cards = []

    for i in values:
        cards.append({
            "value" : i,
            "matched" : False
        })

    return {
        "cards": cards,      
        "flipped": [],      
        "matched_count": 0,
        "game_over": False
    }


def play(game, index):

    if game["cards"][index]["matched"]:
        return game

    if index in game["flipped"]:
        return game

    game["flipped"].append(index)

    if len(game["flipped"]) == 2:

        first = game["flipped"][0]
        second = game["flipped"][1]

        if game["cards"][first]["value"] == game["cards"][second]["value"]:

            game["cards"][first]["matched"] = True
            game["cards"][second]["matched"] = True

            game["matched_count"] += 1

            game["flipped"] = []

            if game["matched_count"] == 8:
                game["game_over"] = True

    return game

def resolve_mismatch(game):
    game["flipped"] = []
    return game
