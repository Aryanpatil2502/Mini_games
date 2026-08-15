let gameOver = false;


async function newGame() {

    const response = await fetch("/api/hangman/new", {
        method: "POST"
    });

    const data = await response.json();

    gameOver = false;

    document.getElementById("word").textContent =
        data.display_word;

    document.getElementById("word-was").textContent = "";

    document.getElementById("guessed-letters").textContent =
        "Guessed letters:";

    document.getElementById("guesses").textContent =
        `Incorrect guesses: 0 / ${data.max_incorrect_guesses}`;

    document.getElementById("hangman-image").src =
        "/static/assets/hangman/hangman_0.svg";

    document.getElementById("result").textContent = "";

    document.getElementById("letter-input").value = "";

    document.getElementById("letter-input").disabled = false;

    document.getElementById("guess-button").disabled = false;

    document.getElementById("letter-input").focus();
}

async function loadGame() {

    const response = await fetch("/api/hangman/current");

    const data = await response.json();

    // No saved game exists
    if (!data.game_exists) {
        newGame();
        return;
    }

    // Load saved game
    gameOver = false;

    document.getElementById("word").textContent =
        data.display_word;

    document.getElementById("guessed-letters").textContent =
        "Guessed letters: " +
        data.guessed_letters.join(" ");

    document.getElementById("guesses").textContent =
        `Incorrect guesses: ${data.incorrect_guesses} / ${data.max_incorrect_guesses}`;

    document.getElementById("hangman-image").src =
        `/static/assets/hangman/hangman_${data.incorrect_guesses}.svg`;

    document.getElementById("result").textContent = "";

    document.getElementById("word-was").textContent = "";

    document.getElementById("letter-input").value = "";

    document.getElementById("letter-input").disabled = false;

    document.getElementById("guess-button").disabled = false;

    // If the saved game was already won
    if (data.won) {

        document.getElementById("result").textContent =
            "You Win!";

        gameOver = true;

        document.getElementById("letter-input").disabled = true;
        document.getElementById("guess-button").disabled = true;

        return;
    }

    // If the saved game was already lost
    if (data.lost) {

        document.getElementById("result").textContent =
            "Game Over!";

        document.getElementById("word-was").textContent =
            `The word was = "${data.word}"`;

        gameOver = true;

        document.getElementById("letter-input").disabled = true;
        document.getElementById("guess-button").disabled = true;

        return;
    }

    document.getElementById("letter-input").focus();
}

async function submitGuess() {

    if (gameOver) {
        return;
    }

    const input = document.getElementById("letter-input");

    const letter = input.value.toLowerCase();



    if (!/^[a-z]$/.test(letter)) {

        input.value = "";

        return;
    }


    const response = await fetch("/api/hangman/guess", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            guess: letter
        })
    });


    const data = await response.json();


    // Show word
    document.getElementById("word").textContent =
        data.display_word;


   
    document.getElementById("guessed-letters").textContent =
        "Guessed letters: " +
        data.guessed_letters.join(" ");



    document.getElementById("guesses").textContent =
        `Incorrect guesses: ${data.incorrect_guesses} / ${data.max_incorrect_guesses}`;


   
    document.getElementById("hangman-image").src =
        `/static/assets/hangman/hangman_${data.incorrect_guesses}.svg`;



    if (data.won) {

        document.getElementById("result").textContent =
            "You Win!";

        gameOver = true;

        input.disabled = true;

        document.getElementById("guess-button").disabled = true;

        return;
    }


   
    if (data.lost) {

        document.getElementById("result").textContent =
            "Game Over!";

        document.getElementById("word-was").textContent =
        `The word was = "${data.word}"`;

        gameOver = true;

        input.disabled = true;

        document.getElementById("guess-button").disabled = true;

        return;
    }



    input.value = "";

    input.focus();
}



document.getElementById("letter-input").addEventListener(
    "keydown",
    function(event) {

        if (event.key === "Enter") {
            submitGuess();
        }

    }
);


loadGame();