// static/js/app.js

// Purpose: Frontend JavaScript for ACM Problem-Solving Platform

// Functionality for interacting with the backend and updating the UI

// Constants
const API_BASE_URL = '/api';

// Utility Functions
function fetchData(endpoint, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    return fetch(`${API_BASE_URL}/${endpoint}`, options)
        .then((response) => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .catch((error) => {
            console.error('Fetch Error:', error);
        });
}

// DOM Manipulation Functions
function renderProblems(problemList) {
    const problemsContainer = document.getElementById('problems-container');
    problemsContainer.innerHTML = '';
    problemList.forEach((problem) => {
        const problemElement = document.createElement('div');
        problemElement.classList.add('problem');
        problemElement.innerHTML = `
            <h3>${problem.title}</h3>
            <p>${problem.description}</p>
            <button onclick="viewProblem(${problem.id})">View Problem</button>
        `;
        problemsContainer.appendChild(problemElement);
    });
}

function renderLeaderboard(leaderboardData) {
    const leaderboardContainer = document.getElementById('leaderboard-container');
    leaderboardContainer.innerHTML = '';
    leaderboardData.forEach((entry, index) => {
        const entryElement = document.createElement('div');
        entryElement.classList.add('leaderboard-entry');
        entryElement.innerHTML = `
            <span>${index + 1}. ${entry.username}</span>
            <span>${entry.score}</span>
        `;
        leaderboardContainer.appendChild(entryElement);
    });
}

// Event Handlers
function viewProblem(problemId) {
    fetchData(`problems/${problemId}`)
        .then((problem) => {
            const problemDetails = document.getElementById('problem-details');
            problemDetails.innerHTML = `
                <h2>${problem.title}</h2>
                <p>${problem.description}</p>
                <textarea id="solution-code" placeholder="Write your solution here..."></textarea>
                <button onclick="submitSolution(${problemId})">Submit Solution</button>
            `;
        });
}

function submitSolution(problemId) {
    const solutionCode = document.getElementById('solution-code').value;
    fetchData(`problems/${problemId}/submit`, 'POST', { solution: solutionCode })
        .then((result) => {
            alert(result.message);
            if (result.success) {
                loadLeaderboard();
            }
        });
}

function loadProblems() {
    fetchData('problems')
        .then((problems) => {
            renderProblems(problems);
        });
}

function loadLeaderboard() {
    fetchData('leaderboard')
        .then((leaderboard) => {
            renderLeaderboard(leaderboard);
        });
}

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    loadProblems();
    loadLeaderboard();
});