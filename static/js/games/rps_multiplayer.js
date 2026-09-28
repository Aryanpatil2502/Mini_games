const socket = io();

const container = document.querySelector(".rps-container");
const myName = container.dataset.username;

const lobby = document.getElementById("lobby");
const waiting = document.getElementById("waiting");
const game = document.getElementById("game");
const resultEl = document.getElementById("result");
const errorEl = document.getElementById("error");
const choiceButtons = document.querySelectorAll(".choice-button");

const restartButton = document.getElementById("restart-button");
const restartRequestPanel = document.getElementById("restart-request");
const restartRequestText = document.getElementById("restart-request-text");
const acceptRestartButton = document.getElementById("accept-restart-button");
const declineRestartButton = document.getElementById("decline-restart-button");

let currentCode = null;
let opponentName = null;
let matchOver = false;


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

function updateScore(wins) {
    const myWins = wins[myName] || 0;
    const opponentWins = wins[opponentName] || 0;

    document.getElementById("score").textContent =
        `${myName}: ${myWins} | ${opponentName}: ${opponentWins}`;
}


// ---------- Lobby buttons ----------

document.getElementById("create-room-button").addEventListener("click", function() {
    errorEl.textContent = "";
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

        if (matchOver) {
            return;
        }

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

    show("waiting");
});

// Both players are in
socket.on("rps_match_ready", function(data) {

    opponentName = data.players.find(function(name) {
        return name !== myName;
    });

    matchOver = false;

    updateScore(data.wins);

    document.getElementById("versus").textContent =
        `Playing against ${opponentName} - first to ${data.wins_needed} wins`;

    resultEl.textContent = "Make your choice!";

    errorEl.textContent = "";
    restartRequestPanel.hidden = true;

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
        outcome = "You win this round!";
    } else {
        outcome = "Opponent wins this round!";
    }

    updateScore(data.wins);

    if (data.match_over) {

        matchOver = true;

        const wonMatch = data.winner === myName;

        resultEl.textContent =
            `You chose ${myChoice}. Opponent chose ${opponentChoice}. ${outcome} `
            + (wonMatch ? "You won the match!" : "Opponent won the match.");

        setChoicesEnabled(false);

        return;
    }

    resultEl.textContent =
        `You chose ${myChoice}. Opponent chose ${opponentChoice}. ${outcome}`;

    setChoicesEnabled(true);
});

// Opponent disconnected mid-match - this client wins by default
socket.on("rps_opponent_left", function(data) {

    matchOver = true;

    resultEl.textContent = "Your opponent left the game. You win by default!";

    setChoicesEnabled(false);
});

socket.on("rps_join_error", function(data) {
    errorEl.textContent = data.error;
    show("lobby");
});

socket.on("disconnect", function() {
    errorEl.textContent = "Connection lost. Refresh the page to reconnect.";
});

function updateScore(wins) {
    const myWins = wins[myName] || 0;
    const opponentWins = wins[opponentName] || 0;

    document.getElementById("score").textContent =
        `${myName}: ${myWins} | ${opponentName}: ${opponentWins}`;
}

// RESTART BUTTON
restartButton.addEventListener("click", function() {
    socket.emit("rps_restart_request", { code: currentCode });
    resultEl.textContent = "Restart request sent...";
});

acceptRestartButton.addEventListener("click", function() {
    socket.emit("rps_restart_response", { code: currentCode, accepted: true });
    restartRequestPanel.hidden = true;
});

declineRestartButton.addEventListener("click", function() {
    socket.emit("rps_restart_response", { code: currentCode, accepted: false });
    restartRequestPanel.hidden = true;
});

socket.on("rps_restart_requested", function(data) {
    restartRequestText.textContent = `${data.from} wants to restart the match.`;
    restartRequestPanel.hidden = false;
});

socket.on("rps_restart_declined", function(data) {
    resultEl.textContent = `${data.by} declined the restart request.`;
});