const socket = io();

const container = document.querySelector(".rps-container");
const myName = container.dataset.username;

const lobby = document.getElementById("lobby");
const waiting = document.getElementById("waiting");
const game = document.getElementById("game");
const resultEl = document.getElementById("result");
const errorEl = document.getElementById("error");
const choiceButtons = document.querySelectorAll(".choice-button");

let currentCode = null;
let myScore = 0;
let opponentScore = 0;
let creatingRoom = false;


function show(section) {
    lobby.hidden = section !== "lobby";
    waiting.hidden = section !== "waiting";
    game.hidden = section !== "game";
}

function setChoicesEnabled(enabled) {
    choiceButtons.forEach(function(button) {
        button.disabled = !enabled;
    });
}

function updateScore() {
    document.getElementById("score").textContent =
        `You: ${myScore} | Opponent: ${opponentScore}`;
}


// ---------- Lobby buttons ----------

document.getElementById("create-room-button").addEventListener("click", function() {
    errorEl.textContent = "";
    creatingRoom = true;
    socket.emit("rps_create_room", {});
});

document.getElementById("join-room-button").addEventListener("click", joinRoom);

document.getElementById("code-input").addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        joinRoom();
    }
});

function joinRoom() {

    const code = document.getElementById("code-input").value.trim().toUpperCase();

    errorEl.textContent = "";

    if (code.length !== 5) {
        errorEl.textContent = "Enter the 5-character room code";
        return;
    }

    socket.emit("rps_join_room", { code: code });
}


// ---------- Choosing ----------

choiceButtons.forEach(function(button) {
    button.addEventListener("click", function() {

        setChoicesEnabled(false);

        resultEl.textContent = "Waiting for opponent...";

        socket.emit("rps_choice_made", {
            code: currentCode,
            choice: button.dataset.choice
        });
    });
});


// ---------- Server events ----------

// Room was created: the creator now joins it as the first player
socket.on("rps_room_created", function(data) {
    socket.emit("rps_join_room", { code: data.code });
});

// We are in the room
socket.on("rps_joined", function(data) {

    currentCode = data.code;

    document.getElementById("room-code").textContent = data.code;

    // Stay on the waiting screen until the match starts
    show("waiting");
});

// Both players are in
socket.on("rps_match_ready", function(data) {

    const opponent = data.players.find(function(name) {
        return name !== myName;
    });

    myScore = 0;
    opponentScore = 0;
    updateScore();

    document.getElementById("versus").textContent = `Playing against ${opponent}`;
    resultEl.textContent = "Make your choice!";

    setChoicesEnabled(true);
    show("game");
});

socket.on("rps_round_result", function(data) {

    const iAmPlayer1 = data.player_1 === myName;

    const myChoice = iAmPlayer1 ? data.choice_1 : data.choice_2;
    const opponentChoice = iAmPlayer1 ? data.choice_2 : data.choice_1;

    let outcome;

    if (data.winner === null) {
        outcome = "It's a tie!";
    } else if (data.winner === myName) {
        outcome = "You win!";
        myScore += 1;
    } else {
        outcome = "Opponent wins!";
        opponentScore += 1;
    }

    resultEl.textContent =
        `You chose ${myChoice}. Opponent chose ${opponentChoice}. ${outcome}`;

    updateScore();

    setChoicesEnabled(true);
});

socket.on("rps_join_error", function(data) {
    errorEl.textContent = data.error;
    show("lobby");
});