// Path: app/static/js/scripts.js
// Purpose: Interface Layer
// Application: ACM Problem-Solving Platform

// Function to toggle visibility of hints
function toggleHint(hintId) {
    const hintElement = document.getElementById(hintId);
    if (hintElement.style.display === "none" || hintElement.style.display === "") {
        hintElement.style.display = "block";
    } else {
        hintElement.style.display = "none";
    }
}

// Function to submit user code
async function submitCode(problemId) {
    const code = document.getElementById(`code-input-${problemId}`).value;

    if (!code) {
        alert("Please enter your code before submitting!");
        return;
    }

    try {
        const response = await fetch(`/submit/${problemId}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ code: code })
        });

        const result = await response.json();

        if (response.ok) {
            alert(`Submission Result: ${result.message}`);
            if (result.success) {
                document.getElementById(`result-${problemId}`).innerText = "Correct!";
                document.getElementById(`result-${problemId}`).classList.add("success");
            } else {
                document.getElementById(`result-${problemId}`).innerText = "Incorrect!";
                document.getElementById(`result-${problemId}`).classList.add("error");
            }
        } else {
            alert(`Error: ${result.message}`);
        }
    } catch (error) {
        console.error("Error during submission:", error);
        alert("An error occurred. Please try again later.");
    }
}

// Function to fetch leaderboard data
async function fetchLeaderboard() {
    try {
        const response = await fetch("/leaderboard");
        const leaderboardData = await response.json();

        if (response.ok) {
            const leaderboardElement = document.getElementById("leaderboard");
            leaderboardElement.innerHTML = "";

            leaderboardData.forEach((entry, index) => {
                const row = document.createElement("tr");

                const rank = document.createElement("td");
                rank.innerText = index + 1;
                row.appendChild(rank);

                const username = document.createElement("td");
                username.innerText = entry.username;
                row.appendChild(username);

                const score = document.createElement("td");
                score.innerText = entry.score;
                row.appendChild(score);

                leaderboardElement.appendChild(row);
            });
        } else {
            console.error("Failed to fetch leaderboard data.");
        }
    } catch (error) {
        console.error("Error fetching leaderboard:", error);
    }
}

// Event listener for code submission buttons
document.addEventListener("DOMContentLoaded", () => {
    const submitButtons = document.querySelectorAll(".submit-button");
    submitButtons.forEach(button => {
        button.addEventListener("click", () => {
            const problemId = button.getAttribute("data-problem-id");
            submitCode(problemId);
        });
    });

    // Automatically fetch leaderboard on page load
    fetchLeaderboard();
});