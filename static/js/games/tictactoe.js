let gameOver = false;


function renderBoard(board) {

    const flatBoard = board.flat();

    const cells = document.querySelectorAll(".cell");

    cells.forEach(function(cell, index) {
        cell.textContent = flatBoard[index];
    });
}


function setBoardEnabled(enabled) {

    const cells = document.querySelectorAll(".cell");

    cells.forEach(function(cell) {
        cell.disabled = !enabled;
    });
}


async function newGame() {

    const response = await fetch("/api/tictactoe/new", {
        method: "POST"
    });

    const data = await response.json();

    gameOver = false;

    renderBoard(data.board);

    document.getElementById("result").textContent = "";

    setBoardEnabled(true);
}


async function loadGame() {

    const response = await fetch("/api/tictactoe/current");

    const data = await response.json();

    // No saved game exists
    if (!data.game_exists) {
        newGame();
        return;
    }

    renderBoard(data.board);

    document.getElementById("result").textContent = "";

    // If the saved game already ended
    if (data.status !== "playing") {

        gameOver = true;

        if (data.status === "draw") {
            document.getElementById("result").textContent =
                "It's a draw!";
        } else if (data.status === "won") {
            document.getElementById("result").textContent =
                "You Win!";
        } else if (data.status === "lost") {
            document.getElementById("result").textContent =
                "You Lose!";
        }

        setBoardEnabled(false);

        return;
    }

    gameOver = false;

    setBoardEnabled(true);
}


async function playMove(index) {

    if (gameOver) {
        return;
    }

    const response = await fetch("/api/tictactoe/move", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            move: index
        })
    });

    const data = await response.json();

    if (data.error) {
        return;
    }

    renderBoard(data.board);

    if (data.status !== "playing") {

        gameOver = true;

        if (data.status === "draw") {
            document.getElementById("result").textContent =
                "It's a draw!";
        } else if (data.status === "won") {
            document.getElementById("result").textContent =
                "You Win!";
        } else if (data.status === "lost") {
            document.getElementById("result").textContent =
                "You Lose!";
        }

        setBoardEnabled(false);
    }
}

loadGame();