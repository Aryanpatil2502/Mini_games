from flask import Flask,render_template,request, jsonify, session
from games.rps.logic import rps

app = Flask(__name__)
app.secret_key = '2502'  

@app.route('/')
def home():
    return render_template('home.html')

@app.route("/rps")
def rps_page():
    return render_template("games/rps.html")

@app.route("/api/rps", methods=["POST"])
def play_rps():

    data = request.get_json()
    player_choice = data["choice"]

    player_score = session.get("player_score", 0)
    computer_score = session.get("computer_score", 0)

    result = rps(player_choice, player_score, computer_score)

    session["player_score"] = result["player_score"]
    session["computer_score"] = result["computer_score"]

    return jsonify(result)

@app.route("/api/rps/reset", methods=["POST"])
def reset_rps():
    session["player_score"] = 0
    session["computer_score"] = 0

    return jsonify({
        "player_score": 0,
        "computer_score": 0
    })

if __name__ == '__main__':
    app.run(debug=True)

