// static/js/app.js

// Purpose: This file is responsible for handling frontend logic for the ACM Problem-Solving Platform.
// It interacts with controllers and renders data dynamically on the frontend.

// Helper function to fetch data from API endpoints
async function fetchData(url, method = 'GET', body = null) {
    try {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
        };

        if (body) {
            options.body = JSON.stringify(body);
        }

        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`Error: ${response.status} ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
    }
}

// Render problems on the homepage
async function renderProblems() {
    const problemsContainer = document.getElementById('problems-container');
    problemsContainer.innerHTML = '<p>Loading...</p>';

    const problems = await fetchData('/problems');
    problemsContainer.innerHTML = '';

    problems.forEach(problem => {
        const problemElement = document.createElement('div');
        problemElement.className = 'problem-item';
        problemElement.innerHTML = `
            <h3>${problem.title}</h3>
            <p>${problem.description}</p>
            <p><strong>Difficulty:</strong> ${problem.difficulty}</p>
            <button onclick="viewProblem(${problem.id})">View More</button>
        `;
        problemsContainer.appendChild(problemElement);
    });
}

// View a specific problem
async function viewProblem(problemId) {
    const problem = await fetchData(`/problems/${problemId}`);
    const problemContainer = document.getElementById('problem-container');
    problemContainer.innerHTML = `
        <h2>${problem.title}</h2>
        <p>${problem.description}</p>
        <p><strong>Difficulty:</strong> ${problem.difficulty}</p>
        <button onclick="submitSolution(${problem.id})">Submit Solution</button>
    `;
}

// Submit solution for a problem
async function submitSolution(problemId) {
    const solutionText = prompt('Enter your solution code:');
    if (!solutionText) {
        alert('Solution cannot be empty!');
        return;
    }

    const result = await fetchData('/solutions', 'POST', {
        problem_id: problemId,
        content: solutionText,
    });

    if (result && result.success) {
        alert('Solution submitted successfully!');
    } else {
        alert('Failed to submit the solution.');
    }
}

// Render users on the leaderboard
async function renderLeaderboard() {
    const leaderboardContainer = document.getElementById('leaderboard-container');
    leaderboardContainer.innerHTML = '<p>Loading...</p>';

    const users = await fetchData('/users');
    leaderboardContainer.innerHTML = '';

    users.forEach(user => {
        const userElement = document.createElement('div');
        userElement.className = 'user-item';
        userElement.innerHTML = `
            <p><strong>${user.username}</strong> - ${user.email}</p>
        `;
        leaderboardContainer.appendChild(userElement);
    });
}

// Initialize the app and set event listeners
document.addEventListener('DOMContentLoaded', () => {
    renderProblems();
    renderLeaderboard();
});