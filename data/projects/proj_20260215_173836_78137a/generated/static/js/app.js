// static/js/app.js

// Frontend JavaScript logic for ACM Problem-Solving Platform

// Utility function to make API calls
async function apiCall(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: data ? JSON.stringify(data) : null,
    };

    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error('API call failed: ' + response.statusText);
        }
        return await response.json();
    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
}

// Event listener for submitting a solution
document.getElementById('submit-solution-btn').addEventListener('click', async () => {
    const problemId = document.getElementById('problem-id').value;
    const code = document.getElementById('code-editor').value;

    if (!problemId || !code) {
        alert('Please select a problem and write a solution.');
        return;
    }

    try {
        const result = await apiCall('/api/solution/submit', 'POST', {
            problem_id: problemId,
            code: code,
        });

        if (result.success) {
            alert('Solution submitted successfully!');
            // Optionally refresh leaderboard or problem status.
        } else {
            alert('Failed to submit solution: ' + result.message);
        }
    } catch (error) {
        alert('Error submitting solution.');
    }
});

// Fetch and display problem details
async function loadProblemDetails(problemId) {
    try {
        const problem = await apiCall(`/api/problem/${problemId}`);
        document.getElementById('problem-title').innerText = problem.title;
        document.getElementById('problem-description').innerText = problem.description;
    } catch (error) {
        alert('Error loading problem details.');
    }
}

// Initialize event listeners for problem selection
document.querySelectorAll('.problem-list-item').forEach(item => {
    item.addEventListener('click', () => {
        const problemId = item.getAttribute('data-problem-id');
        loadProblemDetails(problemId);
    });
});

// Leaderboard refresh function
async function refreshLeaderboard() {
    try {
        const leaderboard = await apiCall('/api/leaderboard');
        const leaderboardContainer = document.getElementById('leaderboard');
        leaderboardContainer.innerHTML = ''; // Clear existing leaderboard

        leaderboard.forEach(entry => {
            const entryElement = document.createElement('li');
            entryElement.textContent = `${entry.username}: ${entry.score} points`;
            leaderboardContainer.appendChild(entryElement);
        });
    } catch (error) {
        alert('Error refreshing leaderboard.');
    }
}

// Load initial data on page load
window.addEventListener('load', () => {
    const firstProblemId = document.querySelector('.problem-list-item').getAttribute('data-problem-id');
    if (firstProblemId) {
        loadProblemDetails(firstProblemId);
    }
    refreshLeaderboard();
});