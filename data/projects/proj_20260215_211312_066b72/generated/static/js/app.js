// static/js/app.js

// Purpose: Frontend functionality for ACM Problem-Solving Platform
// Layer: Frontend

// Ensure code runs after DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('ACM Problem-Solving Platform Loaded');

    // Helper function to fetch data from the backend
    async function fetchData(url, method = 'GET', data = null) {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
        };
        if (data) {
            options.body = JSON.stringify(data);
        }
        const response = await fetch(url, options);
        return response.json();
    }

    // Handle problem selection from problem library
    const problemList = document.querySelector('#problem-list');
    if (problemList) {
        problemList.addEventListener('click', async (event) => {
            const target = event.target;
            if (target.tagName === 'LI' && target.dataset.problemId) {
                const problemId = target.dataset.problemId;
                const problemDetails = await fetchData(`/api/problems/${problemId}`);
                displayProblemDetails(problemDetails);
            }
        });
    }

    // Function to display problem details
    function displayProblemDetails(problemDetails) {
        const problemTitle = document.querySelector('#problem-title');
        const problemDescription = document.querySelector('#problem-description');
        if (problemTitle && problemDescription) {
            problemTitle.textContent = problemDetails.title;
            problemDescription.textContent = problemDetails.description;
        }
    }

    // Handle code submission
    const submitForm = document.querySelector('#submit-form');
    if (submitForm) {
        submitForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const codeInput = document.querySelector('#code-input');
            const problemId = document.querySelector('#problem-id').value;
            if (codeInput && problemId) {
                const code = codeInput.value;
                const result = await fetchData(`/api/problems/${problemId}/submit`, 'POST', { code });
                displaySubmissionResult(result);
            }
        });
    }

    // Function to display submission results
    function displaySubmissionResult(result) {
        const resultContainer = document.querySelector('#submission-result');
        if (resultContainer) {
            resultContainer.textContent = result.message;
            resultContainer.className = result.success ? 'success' : 'error';
        }
    }

    // Initialize leaderboard
    const leaderboardSection = document.querySelector('#leaderboard');
    if (leaderboardSection) {
        async function loadLeaderboard() {
            const leaderboardData = await fetchData('/api/leaderboard');
            populateLeaderboard(leaderboardData);
        }

        function populateLeaderboard(data) {
            const leaderboardList = document.querySelector('#leaderboard-list');
            if (leaderboardList) {
                leaderboardList.innerHTML = '';
                data.forEach((entry) => {
                    const li = document.createElement('li');
                    li.textContent = `${entry.username}: ${entry.score}`;
                    leaderboardList.appendChild(li);
                });
            }
        }

        loadLeaderboard();
    }
});