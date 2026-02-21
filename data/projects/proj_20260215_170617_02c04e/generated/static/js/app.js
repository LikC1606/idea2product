// Module: app_js
// Layer: frontend
// Database: none

// Purpose: Frontend JavaScript for API calls and interactivity

// Function to fetch a list of problems from the API and display them
async function fetchProblems() {
    try {
        const response = await fetch('/api/problems', { method: 'GET' });
        if (response.ok) {
            const problems = await response.json();
            displayProblems(problems);
        } else {
            console.error('Failed to fetch problems');
        }
    } catch (error) {
        console.error('Error fetching problems:', error);
    }
}

// Function to display problems on the page
function displayProblems(problems) {
    const problemsContainer = document.getElementById('problems-container');
    problemsContainer.innerHTML = '';

    problems.forEach(problem => {
        const problemElement = document.createElement('div');
        problemElement.className = 'problem-item';
        problemElement.innerHTML = `
            <h3>${problem.title}</h3>
            <p>${problem.description}</p>
            <a href="/problem/${problem.id}" class="view-problem">View Problem</a>
        `;
        problemsContainer.appendChild(problemElement);
    });
}

// Function for submitting a solution
async function submitSolution(problemId, solutionCode) {
    try {
        const response = await fetch(`/api/solutions/${problemId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ code: solutionCode })
        });

        if (response.ok) {
            const result = await response.json();
            displaySubmissionResult(result);
        } else {
            console.error('Failed to submit solution');
        }
    } catch (error) {
        console.error('Error submitting solution:', error);
    }
}

// Function to display the result of a submission
function displaySubmissionResult(result) {
    const resultContainer = document.getElementById('result-container');
    resultContainer.innerHTML = `
        <h3>Submission Result</h3>
        <p>Status: ${result.status}</p>
        <p>Message: ${result.message}</p>
    `;
}

// Event listener for the problem submission form
document.getElementById('submit-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const problemId = document.getElementById('problem-id').value;
    const solutionCode = document.getElementById('solution-code').value;
    submitSolution(problemId, solutionCode);
});

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    fetchProblems();
});