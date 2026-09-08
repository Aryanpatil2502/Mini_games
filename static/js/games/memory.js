let resolving = false;


function renderBoard(game) {

    const cells = document.querySelectorAll(".cell");

    cells.forEach(function(cell, index) {

        const card = game.cards[index];
        const isFlipped = game.flipped.includes(index);

        cell.classList.remove("matched", "flipped");

        if (card.matched) {
            cell.textContent = card.value;
            cell.classList.add("matched");
            cell.disabled = true;
        } else if (isFlipped) {
            cell.textContent = card.value;
            cell.classList.add("flipped");
            cell.disabled = false;
        } else {
            cell.textContent = "";
            cell.disabled = false;
        }
    });
}


function setBoardEnabled(enabled) {

    const cells = document.querySelectorAll(".cell");

    cells.forEach(function(cell, index) {
        if (!enabled) {
            cell.disabled = true;
        }
    });
}


async function newGame() {

    const response = await fetch("/api/memory/new", {
        method: "POST"
    });

    const data = await response.json();

    resolving = false;

    renderBoard(data);

    document.getElementById("result").textContent = "";
}


async function loadGame() {

    const response = await fetch("/api/memory/current");

    const data = await response.json();

    if (!data.game_exists) {
        newGame();
        return;
    }

    renderBoard(data);

    document.getElementById("result").textContent = "";

    if (data.game_over) {
        document.getElementById("result").textContent = "You matched all pairs!";
        setBoardEnabled(false);
    }

    // If a mismatch was left unresolved (e.g. page refreshed mid-delay),
    // resolve it immediately on load
    if (data.flipped.length === 2) {
        resolving = true;
        setTimeout(async function() {
            await resolveMismatch();
        }, 800);
    }
}


async function resolveMismatch() {

    const response = await fetch("/api/memory/resolve", {
        method: "POST"
    });

    const data = await response.json();

    resolving = false;

    renderBoard(data);
}


async function playMove(index) {

    if (resolving) {
        return;
    }

    const response = await fetch("/api/memory/play", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            index: index
        })
    });

    const data = await response.json();

    if (data.error) {
        return;
    }

    renderBoard(data);

    if (data.game_over) {
        document.getElementById("result").textContent = "You matched all pairs!";
        setBoardEnabled(false);
        return;
    }

    // Two cards flipped and they didn't match — wait, then resolve
    if (data.flipped.length === 2) {
        resolving = true;
        setTimeout(async function() {
            await resolveMismatch();
        }, 800);
    }
}


loadGame();