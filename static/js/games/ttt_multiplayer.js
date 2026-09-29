const socket = io();

const container = document.querySelector(".ttt-container");
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

const restartButton = document.getElementById("restart-button");
const restartRequestPanel = document.getElementById("restart-request");
const restartRequestText = document.getElementById("restart-request-text");
const acceptRestartButton = document.getElementById("accept-restart-button");
const declineRestartButton = document.getElementById("decline-restart-button");


const NEW_GAME_DELAY = 1800;


let currentCode = null;
let opponentName = null;
let currentTurn = null;
let board = ["", "", "", "", "", "", "", "", ""];
let symbols = {};
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

        cell.textContent = board[index];

        cell.disabled =
            board[index] !== "" || !myTurn || matchOver || locked;
    });
}

function updateTurn() {

    if (matchOver) {
        turnEl.textContent = "";
        return;
    }

    if (locked) {
        turnEl.textContent = "";
        return;
    }

    const mySymbol = symbols[myName] || "";

    if (currentTurn === myName) {
        turnEl.textContent = `Your turn (${mySymbol})`;
    } else {
        turnEl.textContent = `${opponentName}'s turn`;
    }
}

function updateScore(wins) {

    scoreEl.textContent =
        `${myName}: ${wins[myName] || 0} | ${opponentName}: ${wins[opponentName] || 0}`;
}

function updateVersus(winsNeeded) {

    const mySymbol = symbols[myName] || "";

    versusEl.textContent =
        `Playing against ${opponentName} - first to ${winsNeeded} game wins` +
        (mySymbol ? ` - you are ${mySymbol}` : "");
}


document.getElementById("create-room-button").addEventListener("click", function() {
    errorEl.textContent = "";
    socket.emit("ttt_create_room", {});
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

    socket.emit("ttt_join_room", { code: code });
}

let winsNeeded = 5;

cells.forEach(function(cell) {

    cell.addEventListener("click", function() {

        if (matchOver || locked) {
            return;
        }

        if (currentTurn !== myName) {
            return;
        }

        const index = Number(cell.dataset.index);

        if (board[index] !== "") {
            return;
        }

        socket.emit("ttt_move", {
            code: currentCode,
            move: index
        });
    });
});

socket.on("ttt_room_created", function(data) {
    socket.emit("ttt_join_room", { code: data.code });
});

socket.on("ttt_joined", function(data) {

    currentCode = data.code;

    document.getElementById("room-code").textContent = data.code;

    show("waiting");
});

socket.on("ttt_match_ready", function(data) {

    cancelNewGameTimer();

    opponentName = data.players.find(function(name) {
        return name !== myName;
    });

    board = data.board.flat();
    symbols = data.symbols;
    currentTurn = data.current_turn;
    winsNeeded = data.wins_needed;
    matchOver = false;

    resultEl.textContent = "";
    errorEl.textContent = "";
    restartRequestPanel.hidden = true;

    updateVersus(winsNeeded);
    updateScore(data.wins);
    updateTurn();
    renderBoard();

    show("game");
});

socket.on("ttt_move_result", function(data) {

    board = data.board.flat();
    symbols = data.symbols;
    currentTurn = data.current_turn;
    matchOver = data.match_over;

    if (data.game_over) {

        let gameOutcome;

        if (data.winner_username === myName) {
            gameOutcome = "You won that game!";
        } else if (data.winner_username) {
            gameOutcome = `${opponentName} won that game.`;
        } else {
            gameOutcome = "That game was a draw.";
        }

        if (data.match_over) {

            const iWonMatch = data.wins[myName] > data.wins[opponentName];

            resultEl.textContent =
                gameOutcome + (iWonMatch ? " You won the match!" : ` ${opponentName} won the match.`);

        } else {

            resultEl.textContent = gameOutcome + " Next game starting...";

            // Keep the board frozen until ttt_new_game is applied
            locked = true;
        }

    } else {
        resultEl.textContent = "";
    }

    updateScore(data.wins);
    updateTurn();
    renderBoard();
});

socket.on("ttt_new_game", function(data) {

    if (newGameTimer !== null) {
        clearTimeout(newGameTimer);
    }

    newGameTimer = setTimeout(function() {

        newGameTimer = null;
        locked = false;

        board = data.board.flat();
        symbols = data.symbols;
        currentTurn = data.current_turn;

        resultEl.textContent = "";

        updateVersus(winsNeeded);
        updateTurn();
        renderBoard();

    }, NEW_GAME_DELAY);
});

socket.on("ttt_opponent_left", function(data) {

    cancelNewGameTimer();

    matchOver = true;

    resultEl.textContent = "Your opponent left the game. You win by default!";

    updateTurn();
    renderBoard();
});

socket.on("ttt_join_error", function(data) {
    errorEl.textContent = data.error;
    show("lobby");
});

socket.on("disconnect", function() {
    errorEl.textContent = "Connection lost. Refresh the page to reconnect.";
});

restartButton.addEventListener("click", function() {
    socket.emit("ttt_restart_request", { code: currentCode });
    resultEl.textContent = "Restart request sent...";
});

acceptRestartButton.addEventListener("click", function() {
    socket.emit("ttt_restart_response", { code: currentCode, accepted: true });
    restartRequestPanel.hidden = true;
});

declineRestartButton.addEventListener("click", function() {
    socket.emit("ttt_restart_response", { code: currentCode, accepted: false });
    restartRequestPanel.hidden = true;
});

socket.on("ttt_restart_requested", function(data) {
    restartRequestText.textContent = `${data.from} wants to restart the match.`;
    restartRequestPanel.hidden = false;
});

socket.on("ttt_restart_declined", function(data) {
    resultEl.textContent = `${data.by} declined the restart request.`;
});