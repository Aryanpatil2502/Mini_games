async function playGame(choice) {

    const response = await fetch("/api/rps", {
        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            choice: choice
        })
    });

    const data = await response.json();

    document.getElementById("result").textContent =
        `You chose ${data.player}. Computer chose ${data.computer}. ${data.result}`;

    document.getElementById("score").textContent =
    `Player: ${data.player_score} | Computer: ${data.computer_score}`;
}

async function resetGame() {
    const response = await fetch("/api/rps/reset", {
        method: "POST"
    });

    const data = await response.json();

    document.getElementById("score").textContent =
        `Player: ${data.player_score} | Computer: ${data.computer_score}`;

    document.getElementById("result").textContent = "";
}