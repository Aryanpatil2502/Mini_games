const socket = io();

const container = document.querySelector(".memory-container");
const myName = container.dataset.username;

const lobby = document.getElementById("lobby");
const waiting = document.getElementById("waiting");
const game = document.getElementById("game");
const resultEl = document.getElementById("result");
const errorEl = document.getElementById("error");

const cells = document.querySelectorAll(".cell");
const versusEl = document.getElementById("versus");
const turnEl = document.getElementById("turn-indicator");
const scoreEl = document.getElementById("score");
const gameWinsEl = document.getElementById("game-wins");

const restartButton = document.getElementById("restart-button");
const restartRequestPanel = document.getElementById("restart-request");
const restartRequestText = document.getElementById("restart-request-text");
const acceptRestartButton = document.getElementById("accept-restart-button");
const declineRestartButton = document.getElementById("decline-restart-button");

const NEW_GAME_DELAY = 1800;


let currentCode = null;
let opponentName = null;
let currentTurn = null;
let cards = [];
let flipped = [];
let lastWins = {};
let matchOver = false;
let locked = false;
let newGameTimer = null;


function show(section) {
    lobby.hidden = section !== "lobby";
    waiting.hidden = section !== "waiting";
    game.hidden = section !== "game";
}

function cancelNewGameTimer() {
    if (newGameTimer !== null) {
        clearTimeout(newGameTimer);
        newGameTimer = null;
    }
    locked = false;
}

function renderBoard() {

    const myTurn = currentTurn === myName;

    cells.forEach(function(cell, index) {

        const card = cards[index];
        const isFlipped = flipped.includes(index);

        cell.classList.remove("matched", "flipped");

        if (card.matched) {
            cell.textContent = card.value;
            cell.classList.add("matched");
            cell.disabled = true;

        } else if (isFlipped) {
            cell.textContent = card.value;
            cell.classList.add("flipped");
            cell.disabled = true;

        } else {
            cell.textContent = "";
            cell.disabled = !myTurn || flipped.length >= 2 || matchOver || locked;
        }
    });
}

function updateTurn() {

    if (matchOver || locked) {
        turnEl.textContent = "";
        return;
    }

    if (currentTurn === myName) {
        turnEl.textContent = "Your turn";
    } else {
        turnEl.textContent = `${opponentName}'s turn`;
    }
}

function updateScores(pairs, wins) {

    scoreEl.textContent =
        `Pairs this game - ${myName}: ${pairs[myName] || 0} | ${opponentName}: ${pairs[opponentName] || 0}`;

    gameWinsEl.textContent =
        `Games won - ${myName}: ${wins[myName] || 0} | ${opponentName}: ${wins[opponentName] || 0}`;
}

document.getElementById("create-room-button").addEventListener("click", function() {
    errorEl.textContent = "";
    socket.emit("memory_create_room", {});
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

    socket.emit("memory_join_room", { code: code });
}


cells.forEach(function(cell) {

    cell.addEventListener("click", function() {

        if (matchOver || locked) {
            return;
        }

        if (currentTurn !== myName) {
            return;
        }

        if (flipped.length >= 2) {
            return;
        }

        socket.emit("memory_flip_card", {
            code: currentCode,
            index: Number(cell.dataset.index)
        });
    });
});


socket.on("memory_room_created", function(data) {
    socket.emit("memory_join_room", { code: data.code });
});

socket.on("memory_joined", function(data) {

    currentCode = data.code;

    document.getElementById("room-code").textContent = data.code;

    show("waiting");
});

socket.on("memory_match_ready", function(data) {

    cancelNewGameTimer();

    opponentName = data.players.find(function(name) {
        return name !== myName;
    });

    cards = data.cards;
    flipped = [];
    currentTurn = data.current_turn;
    lastWins = data.wins;
    matchOver = false;

    versusEl.textContent =
        `Playing against ${opponentName} - first to ${data.wins_needed} game wins`;

    resultEl.textContent = "";
    errorEl.textContent = "";
    restartRequestPanel.hidden = true;

    updateScores({}, data.wins);
    updateTurn();
    renderBoard();

    show("game");
});

socket.on("memory_flip_result", function(data) {

    cards = data.cards;
    flipped = data.flipped;
    currentTurn = data.current_turn;
    matchOver = data.match_over;

    if (data.game_over) {

        const myWinsNow = data.wins[myName] || 0;
        const oppWinsNow = data.wins[opponentName] || 0;
        const myWinsBefore = lastWins[myName] || 0;
        const oppWinsBefore = lastWins[opponentName] || 0;

        let gameOutcome;

        if (myWinsNow > myWinsBefore) {
            gameOutcome = "You won that game!";
        } else if (oppWinsNow > oppWinsBefore) {
            gameOutcome = `${opponentName} won that game.`;
        } else {
            gameOutcome = "That game was a draw.";
        }

        if (data.match_over) {
            const iWonMatch = myWinsNow > oppWinsNow;

            resultEl.textContent =
                gameOutcome + (iWonMatch ? " You won the match!" : " " + opponentName + " won the match.");
        } else {
            resultEl.textContent = gameOutcome + " Next game starting...";

            locked = true;
        }

    } else if (flipped.length === 2) {
        resultEl.textContent = "No match!";
    } else {
        resultEl.textContent = "";
    }

    lastWins = data.wins;

    updateScores(data.pairs_found, data.wins);
    updateTurn();
    renderBoard();

    if (!matchOver && flipped.length === 2 && currentTurn === myName) {
        setTimeout(function() {
            socket.emit("memory_resolve_mismatch", { code: currentCode });
        }, 1000);
    }
});

socket.on("memory_new_game", function(data) {

    if (newGameTimer !== null) {
        clearTimeout(newGameTimer);
    }

    newGameTimer = setTimeout(function() {

        newGameTimer = null;
        locked = false;

        cards = data.cards;
        flipped = [];
        currentTurn = data.current_turn;

        resultEl.textContent = "";

        updateTurn();
        renderBoard();

    }, NEW_GAME_DELAY);
});

socket.on("memory_opponent_left", function(data) {

    cancelNewGameTimer();

    matchOver = true;

    resultEl.textContent = "Your opponent left the game. You win by default!";

    updateTurn();
    renderBoard();
});

socket.on("memory_join_error", function(data) {
    errorEl.textContent = data.error;
    show("lobby");
});

socket.on("disconnect", function() {
    errorEl.textContent = "Connection lost. Refresh the page to reconnect.";
});


restartButton.addEventListener("click", function() {
    socket.emit("memory_restart_request", { code: currentCode });
    resultEl.textContent = "Restart request sent...";
});

acceptRestartButton.addEventListener("click", function() {
    socket.emit("memory_restart_response", { code: currentCode, accepted: true });
    restartRequestPanel.hidden = true;
});

declineRestartButton.addEventListener("click", function() {
    socket.emit("memory_restart_response", { code: currentCode, accepted: false });
    restartRequestPanel.hidden = true;
});

socket.on("memory_restart_requested", function(data) {
    restartRequestText.textContent = `${data.from} wants to restart the match.`;
    restartRequestPanel.hidden = false;
});

socket.on("memory_restart_declined", function(data) {
    resultEl.textContent = `${data.by} declined the restart request.`;
});