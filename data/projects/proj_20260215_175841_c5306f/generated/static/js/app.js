// static/js/app.js

// Frontend JavaScript for ACM Problem-Solving Platform

// DOM Elements
const problemList = document.getElementById('problem-list');
const submitButton = document.getElementById('submit-button');
const codeInput = document.getElementById('code-input');
const resultDisplay = document.getElementById('result-display');
const leaderboard = document.getElementById('leaderboard');
const userProfile = document.getElementById('user-profile');

// Utility Functions
function fetchProblems() {
    fetch('/api/problems')
        .then(response => response.json())
        .then(data => renderProblemList(data))
        .catch(error => console.error('Error fetching problems:', error));
}

function renderProblemList(problems) {
    problemList.innerHTML = problems.map(problem => `
        <li class="problem-item" data-id="${problem.id}">
            ${problem.title}
        </li>
    `).join('');
}

function submitSolution(problemId, code) {
    fetch(`/api/problems/${problemId}/submit`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code: code }),
    })
    .then(response => response.json())
    .then(data => displayResult(data))
    .catch(error => console.error('Error submitting solution:', error));
}

function displayResult(result) {
    if (result.success) {
        resultDisplay.textContent = 'Success! Your solution is correct.';
        resultDisplay.classList.add('success');
    } else {
        resultDisplay.textContent = `Error: ${result.error}`;
        resultDisplay.classList.add('error');
    }
}

function fetchLeaderboard() {
    fetch('/api/leaderboard')
        .then(response => response.json())
        .then(data => renderLeaderboard(data))
        .catch(error => console.error('Error fetching leaderboard:', error));
}

function renderLeaderboard(data) {
    leaderboard.innerHTML = data.map(entry => `
        <li>
            ${entry.username} - ${entry.score} points
        </li>
    `).join('');
}

function fetchUserProfile(userId) {
    fetch(`/api/users/${userId}`)
        .then(response => response.json())
        .then(data => renderUserProfile(data))
        .catch(error => console.error('Error fetching user profile:', error));
}

function renderUserProfile(user) {
    userProfile.innerHTML = `
        <h2>${user.username}</h2>
        <p>${user.bio}</p>
        <p>Score: ${user.score}</p>
    `;
}

// Event Listeners
problemList.addEventListener('click', event => {
    const problemItem = event.target.closest('.problem-item');
    if (problemItem) {
        const problemId = problemItem.getAttribute('data-id');
        const code = codeInput.value;
        submitSolution(problemId, code);
    }
});

submitButton.addEventListener('click', () => {
    const selectedProblem = document.querySelector('.problem-item.selected');
    if (selectedProblem) {
        const problemId = selectedProblem.getAttribute('data-id');
        const code = codeInput.value;
        submitSolution(problemId, code);
    }
});

// Initialize Page
fetchProblems();
fetchLeaderboard();