// static/js/app.js

// Frontend JavaScript for the ACM Problem-Solving Platform

// Function to fetch problems from the backend
async function fetchProblems() {
    try {
        const response = await fetch('/api/problems');
        const problems = await response.json();
        renderProblems(problems);
    } catch (error) {
        console.error('Error fetching problems:', error);
    }
}

// Function to render problems on the page
function renderProblems(problems) {
    const problemContainer = document.getElementById('problem-container');
    problemContainer.innerHTML = '';

    problems.forEach(problem => {
        const problemElement = document.createElement('div');
        problemElement.className = 'problem-item';
        problemElement.innerHTML = `
            <h3>${problem.title}</h3>
            <p>${problem.description}</p>
            <button onclick="viewProblem(${problem.id})">View Details</button>
        `;
        problemContainer.appendChild(problemElement);
    });
}

// Function to fetch and display a specific problem
async function viewProblem(problemId) {
    try {
        const response = await fetch(`/api/problems/${problemId}`);
        const problem = await response.json();
        displayProblemDetails(problem);
    } catch (error) {
        console.error('Error fetching problem details:', error);
    }
}

// Function to display problem details
function displayProblemDetails(problem) {
    const problemDetailsContainer = document.getElementById('problem-details-container');
    problemDetailsContainer.innerHTML = `
        <h2>${problem.title}</h2>
        <p>${problem.description}</p>
        <textarea id="solution-code" placeholder="Write your solution here..."></textarea>
        <button onclick="submitSolution(${problem.id})">Submit Solution</button>
    `;
    problemDetailsContainer.style.display = 'block';
}

// Function to submit a solution
async function submitSolution(problemId) {
    const solutionCode = document.getElementById('solution-code').value;

    try {
        const response = await fetch(`/api/solutions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ problem_id: problemId, code: solutionCode })
        });

        const result = await response.json();
        if (response.ok) {
            alert('Solution submitted successfully!');
        } else {
            alert(`Error: ${result.error}`);
        }
    } catch (error) {
        console.error('Error submitting solution:', error);
    }
}

// Initial function to load problems when the page loads
document.addEventListener('DOMContentLoaded', () => {
    fetchProblems();
});