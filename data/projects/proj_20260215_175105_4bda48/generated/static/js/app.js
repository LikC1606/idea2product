// static/js/app.js
document.addEventListener("DOMContentLoaded", () => {
    // Global Variables
    const problemListContainer = document.getElementById('problem-list');
    const userProfileContainer = document.getElementById('user-profile');
    const leaderboardContainer = document.getElementById('leaderboard');
    const codeEditor = document.getElementById('code-editor');
    const submissionButton = document.getElementById('submit-code');
    const resultContainer = document.getElementById('result');

    // Fetch Problems and Populate Problem Library
    async function fetchProblems() {
        try {
            const response = await fetch('/problems');
            const problems = await response.json();

            problemListContainer.innerHTML = problems.map(problem => `
                <div class="problem-item" data-id="${problem.id}">
                    <h3>${problem.title}</h3>
                    <p>${problem.description}</p>
                </div>
            `).join('');
        } catch (error) {
            console.error("Error fetching problems:", error);
        }
    }

    // Fetch User Profile Data
    async function fetchUserProfile() {
        try {
            const response = await fetch('/user/profile');
            const user = await response.json();

            userProfileContainer.innerHTML = `
                <h2>${user.name}</h2>
                <p>Rank: ${user.rank}</p>
                <p>Problems Solved: ${user.problems_solved}</p>
            `;
        } catch (error) {
            console.error("Error fetching user profile:", error);
        }
    }

    // Fetch Leaderboard
    async function fetchLeaderboard() {
        try {
            const response = await fetch('/leaderboard');
            const leaderboard = await response.json();

            leaderboardContainer.innerHTML = leaderboard.map((entry, index) => `
                <div class="leaderboard-entry">
                    <span>${index + 1}. ${entry.user}</span>
                    <span>${entry.points} pts</span>
                </div>
            `).join('');
        } catch (error) {
            console.error("Error fetching leaderboard:", error);
        }
    }

    // Submit Code
    async function submitCode() {
        const selectedProblemId = document.querySelector('.problem-item.selected')?.dataset.id;
        const code = codeEditor.value;

        if (!selectedProblemId || !code) {
            alert("Please select a problem and write some code before submitting.");
            return;
        }

        try {
            const response = await fetch(`/problems/${selectedProblemId}/submit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ code })
            });

            const result = await response.json();
            resultContainer.innerHTML = `
                <h3>Submission Result</h3>
                <p>Status: ${result.status}</p>
                <p>Message: ${result.message}</p>
            `;
        } catch (error) {
            console.error("Error submitting code:", error);
        }
    }

    // Event Listeners
    problemListContainer.addEventListener('click', (event) => {
        const problemItem = event.target.closest('.problem-item');
        if (problemItem) {
            document.querySelectorAll('.problem-item').forEach(item => item.classList.remove('selected'));
            problemItem.classList.add('selected');
        }
    });

    submissionButton.addEventListener('click', submitCode);

    // Initial Data Fetch
    fetchProblems();
    fetchUserProfile();
    fetchLeaderboard();
});