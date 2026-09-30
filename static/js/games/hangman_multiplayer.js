const socket = io();

const container = document.querySelector(".hangman-container");
const myName = container.dataset.username;

const lobby = document.getElementById("lobby");
const waiting = document.getElementById("waiting");
const game = document.getElementById("game");
const resultEl = document.getElementById("result");
const errorEl = document.getElementById("error");

const versusEl = document.getElementById("versus");
const gameWinsEl = document.getElementById("game-wins");
const timerEl = document.getElementById("timer");

const myWordEl = document.getElementById("my-word");
const myGuessedEl = document.getElementById("my-guessed");
const myLivesEl = document.getElementById("my-lives");
const myStatusEl = document.getElementById("my-status");

const opponentNameEl = document.getElementById("opponent-name");
const opponentLivesEl = document.getElementById("opponent-lives");
const opponentStatusEl = document.getElementById("opponent-status");

const letterInput = document.getElementById("letter-input");
const guessButton = document.getElementById("guess-button");

const restartButton = document.getElementById("restart-button");
const restartRequestPanel = document.getElementById("restart-request");
const restartRequestText = document.getElementById("restart-request-text");
const acceptRestartButton = document.getElementById("accept-restart-button");
const declineRestartButton = document.getElementById("decline-restart-button");

const NEW_GAME_DELAY = 1800;


let currentCode = null;
let opponentName = null;
let matchOver = false;
let locked = false;
let newGameTimer = null;
let countdownInterval = null;


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

function stopCountdown() {
    if (countdownInterval !== null) {
        clearInterval(countdownInterval);
        countdownInterval = null;
    }
}

function startCountdown(roundStartTime, roundTimeLimit) {

    stopCountdown();

    function tick() {

        const elapsed = (Date.now() / 1000) - roundStartTime;
        const remaining = Math.max(0, Math.ceil(roundTimeLimit - elapsed));

        timerEl.textContent = `Time left: ${remaining}s`;

        if (remaining <= 0) {
            stopCountdown();
        }
    }

    tick();
    countdownInterval = setInterval(tick, 250);
}

function renderStates(myState, opponentState) {

    myWordEl.textContent = myState.display_word.split("").join(" ");
    myGuessedEl.textContent = "Guessed: " + myState.guessed_letters.join(" ");
    myLivesEl.textContent =
        `Lives left: ${myState.max_incorrect_guesses - myState.incorrect_guesses} / ${myState.max_incorrect_guesses}`;

    if (myState.status === "won") {
        myStatusEl.textContent = "You solved it!";
    } else if (myState.status === "lost") {
        myStatusEl.textContent = "Out of lives or time!";
    } else {
        myStatusEl.textContent = "";
    }

    if (opponentState) {
        opponentLivesEl.textContent =
            `Lives left: ${opponentState.max_incorrect_guesses - opponentState.incorrect_guesses} / ${opponentState.max_incorrect_guesses}`;

        if (opponentState.status === "won") {
            opponentStatusEl.textContent = "Solved it!";
        } else if (opponentState.status === "lost") {
            opponentStatusEl.textContent = "Out of lives or time!";
        } else {
            opponentStatusEl.textContent = "Still guessing...";
        }
    }

    const canGuess = myState.status === "playing" && !matchOver && !locked;

    letterInput.disabled = !canGuess;
    guessButton.disabled = !canGuess;
}

function updateGameWins(wins) {
    gameWinsEl.textContent =
        `Games won - ${myName}: ${wins[myName] || 0} | ${opponentName}: ${wins[opponentName] || 0}`;
}


document.getElementById("create-room-button").addEventListener("click", function() {
    errorEl.textContent = "";
    socket.emit("hangman_create_room", {});
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

    socket.emit("hangman_join_room", { code: code });
}


function submitGuess() {

    if (matchOver || locked) {
        return;
    }

    const letter = letterInput.value.toLowerCase();

    if (!/^[a-z]$/.test(letter)) {
        letterInput.value = "";
        return;
    }

    socket.emit("hangman_guess_letter", {
        code: currentCode,
        letter: letter
    });

    letterInput.value = "";
    letterInput.focus();
}

guessButton.addEventListener("click", submitGuess);

letterInput.addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        submitGuess();
    }
});


socket.on("hangman_room_created", function(data) {
    socket.emit("hangman_join_room", { code: data.code });
});

socket.on("hangman_joined", function(data) {

    currentCode = data.code;

    document.getElementById("room-code").textContent = data.code;

    show("waiting");
});

socket.on("hangman_match_ready", function(data) {

    cancelNewGameTimer();
    stopCountdown();

    opponentName = data.players.find(function(name) {
        return name !== myName;
    });

    opponentNameEl.textContent = opponentName;

    matchOver = false;

    versusEl.textContent =
        `Playing against ${opponentName} - first to ${data.wins_needed} game wins`;

    resultEl.textContent = "";
    errorEl.textContent = "";
    restartRequestPanel.hidden = true;

    updateGameWins(data.wins);
    renderStates(data.my_state, data.opponent_state);
    startCountdown(data.round_start_time, data.round_time_limit);

    show("game");
});

socket.on("hangman_guess_result", function(data) {

    renderStates(data.my_state, data.opponent_state);
    updateGameWins(data.wins);

    matchOver = data.match_over;

    if (data.round_over) {

        stopCountdown();

        let outcome;

        if (data.round_winner === "draw") {
            outcome = `That round was a draw. The word was "${data.word}".`;
        } else if (data.round_winner === myName) {
            outcome = `You won that round! The word was "${data.word}".`;
        } else {
            outcome = `${opponentName} won that round. The word was "${data.word}".`;
        }

        if (data.match_over) {

            const iWonMatch = (data.wins[myName] || 0) > (data.wins[opponentName] || 0);

            resultEl.textContent =
                outcome + (iWonMatch ? " You won the match!" : ` ${opponentName} won the match.`);

        } else {
            resultEl.textContent = outcome + " Next round starting...";
            locked = true;
            letterInput.disabled = true;
            guessButton.disabled = true;
        }

    } else {
        resultEl.textContent = "";
    }
});

socket.on("hangman_new_game", function(data) {

    if (newGameTimer !== null) {
        clearTimeout(newGameTimer);
    }

    newGameTimer = setTimeout(function() {

        newGameTimer = null;
        locked = false;

        resultEl.textContent = "";

        renderStates(data.my_state, data.opponent_state);
        startCountdown(data.round_start_time, data.round_time_limit);

    }, NEW_GAME_DELAY);
});

socket.on("hangman_opponent_left", function(data) {

    cancelNewGameTimer();
    stopCountdown();

    matchOver = true;

    resultEl.textContent = "Your opponent left the game. You win by default!";

    letterInput.disabled = true;
    guessButton.disabled = true;
});

socket.on("hangman_join_error", function(data) {
    errorEl.textContent = data.error;
    show("lobby");
});

socket.on("disconnect", function() {
    errorEl.textContent = "Connection lost. Refresh the page to reconnect.";
});


restartButton.addEventListener("click", function() {
    socket.emit("hangman_restart_request", { code: currentCode });
    resultEl.textContent = "Restart request sent...";
});

acceptRestartButton.addEventListener("click", function() {
    socket.emit("hangman_restart_response", { code: currentCode, accepted: true });
    restartRequestPanel.hidden = true;
});

declineRestartButton.addEventListener("click", function() {
    socket.emit("hangman_restart_response", { code: currentCode, accepted: false });
    restartRequestPanel.hidden = true;
});

socket.on("hangman_restart_requested", function(data) {
    restartRequestText.textContent = `${data.from} wants to restart the match.`;
    restartRequestPanel.hidden = false;
});

socket.on("hangman_restart_declined", function(data) {
    resultEl.textContent = `${data.by} declined the restart request.`;
});