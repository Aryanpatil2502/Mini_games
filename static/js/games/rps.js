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

function resetGame() {
    fetch("/api/rps/reset", {
        method: "POST"
    })
    .then(response => response.json())
    .then(data => {

        document.getElementById("score").textContent =
            `Player: ${data.player_score} | Computer: ${data.computer_score}`;

        document.getElementById("result").textContent = "";
    });
}


