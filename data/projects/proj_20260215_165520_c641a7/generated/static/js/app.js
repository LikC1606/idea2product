// static/js/app.js

// Frontend JavaScript for API calls and interactivity

// Function to make API call to fetch problems
async function fetchProblems() {
    try {
        const response = await fetch('/api/problems');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const problems = await response.json();
        renderProblems(problems);
    } catch (error) {
        console.error('Error fetching problems:', error);
    }
}

// Function to make API call to submit a solution
async function submitSolution(problemId, solutionCode) {
    try {
        const response = await fetch(`/api/problems/${problemId}/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ solution: solutionCode }),
        });
        const result = await response.json();
        handleSubmissionResult(result);
    } catch (error) {
        console.error('Error submitting solution:', error);
    }
}

// Function to render problems on the page
function renderProblems(problems) {
    const problemList = document.getElementById('problem-list');
    problemList.innerHTML = ''; // Clear existing problems
    problems.forEach((problem) => {
        const problemItem = document.createElement('div');
        problemItem.className = 'problem-item';
        problemItem.innerHTML = `
            <h3>${problem.title}</h3>
            <p>${problem.description}</p>
            <button onclick="viewProblem(${problem.id})">View</button>
        `;
        problemList.appendChild(problemItem);
    });
}

// Function to handle submission result
function handleSubmissionResult(result) {
    const resultMessage = document.getElementById('result-message');
    if (result.success) {
        resultMessage.textContent = 'Solution submitted successfully!';
        resultMessage.style.color = 'green';
    } else {
        resultMessage.textContent = `Error: ${result.error}`;
        resultMessage.style.color = 'red';
    }
}

// Function to view a specific problem
function viewProblem(problemId) {
    window.location.href = `/problem/${problemId}`;
}

// Function to initialize event listeners and fetch initial data
function initApp() {
    document.getElementById('fetch-problems-btn').addEventListener('click', fetchProblems);
}

// Initialize the app on page load
window.addEventListener('DOMContentLoaded', initApp);