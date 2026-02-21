// static/js/app.js

// Function to fetch problems from the server
async function fetchProblems() {
    try {
        const response = await fetch('/problems');
        if (!response.ok) {
            throw new Error('Failed to fetch problems');
        }
        const problems = await response.json();
        renderProblems(problems);
    } catch (error) {
        console.error('Error fetching problems:', error);
    }
}

// Function to render problems list
function renderProblems(problems) {
    const problemsContainer = document.getElementById('problems-container');
    problemsContainer.innerHTML = '';

    problems.forEach(problem => {
        const problemElement = document.createElement('div');
        problemElement.classList.add('problem');
        problemElement.innerHTML = `
            <h3>${problem.title}</h3>
            <p>${problem.description}</p>
            <button onclick="viewProblem(${problem.id})">View</button>
        `;
        problemsContainer.appendChild(problemElement);
    });
}

// Function to view a specific problem
async function viewProblem(problemId) {
    try {
        const response = await fetch(`/problems/${problemId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch problem');
        }
        const problem = await response.json();
        renderProblemDetails(problem);
    } catch (error) {
        console.error('Error fetching problem:', error);
    }
}

// Function to render problem details
function renderProblemDetails(problem) {
    const problemDetailsContainer = document.getElementById('problem-details-container');
    problemDetailsContainer.innerHTML = `
        <h2>${problem.title}</h2>
        <p>${problem.description}</p>
        <button onclick="submitSolution(${problem.id})">Submit Solution</button>
    `;
}

// Function to submit a solution
async function submitSolution(problemId) {
    const solutionContent = prompt('Enter your solution:');
    if (!solutionContent) {
        alert('Solution cannot be empty.');
        return;
    }

    try {
        const response = await fetch('/solutions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ problem_id: problemId, content: solutionContent })
        });

        if (!response.ok) {
            throw new Error('Failed to submit solution');
        }
        alert('Solution submitted successfully!');
    } catch (error) {
        console.error('Error submitting solution:', error);
    }
}

// Function to fetch and render leaderboard
async function fetchLeaderboard() {
    try {
        const response = await fetch('/leaderboard');
        if (!response.ok) {
            throw new Error('Failed to fetch leaderboard');
        }
        const leaderboard = await response.json();
        renderLeaderboard(leaderboard);
    } catch (error) {
        console.error('Error fetching leaderboard:', error);
    }
}

// Function to render leaderboard
function renderLeaderboard(leaderboard) {
    const leaderboardContainer = document.getElementById('leaderboard-container');
    leaderboardContainer.innerHTML = '';

    leaderboard.forEach(user => {
        const userElement = document.createElement('div');
        userElement.classList.add('leaderboard-entry');
        userElement.innerHTML = `
            <p><strong>${user.username}</strong>: ${user.points} points</p>
        `;
        leaderboardContainer.appendChild(userElement);
    });
}

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    fetchProblems();
    fetchLeaderboard();
});