// static/js/app.js

// Frontend JavaScript for ACM Problem-Solving Platform

// Helper function to make API requests
async function apiRequest(endpoint, method = 'GET', body = null) {
    const headers = { 'Content-Type': 'application/json' };
    const options = { method, headers };
    if (body) {
        options.body = JSON.stringify(body);
    }

    const response = await fetch(endpoint, options);
    if (!response.ok) {
        console.error(`API request failed: ${response.statusText}`);
        throw new Error(`Request failed with status ${response.status}`);
    }
    return await response.json();
}

// Fetch and display problems
async function fetchProblems() {
    try {
        const problems = await apiRequest('/api/problems', 'GET');
        const problemsContainer = document.getElementById('problems-list');
        problemsContainer.innerHTML = '';
        problems.forEach(problem => {
            const problemElement = document.createElement('div');
            problemElement.className = 'problem-item';
            problemElement.innerHTML = `
                <h3>${problem.title}</h3>
                <p>${problem.description}</p>
                <button onclick="viewProblem(${problem.id})">View Problem</button>
            `;
            problemsContainer.appendChild(problemElement);
        });
    } catch (error) {
        console.error('Error fetching problems:', error);
    }
}

// View a specific problem
async function viewProblem(problemId) {
    try {
        const problem = await apiRequest(`/api/problems/${problemId}`, 'GET');
        const problemContainer = document.getElementById('problem-details');
        problemContainer.innerHTML = `
            <h2>${problem.title}</h2>
            <p>${problem.description}</p>
            <textarea id="solution-code" placeholder="Write your solution here"></textarea>
            <button onclick="submitSolution(${problem.id})">Submit Solution</button>
        `;
    } catch (error) {
        console.error('Error fetching problem details:', error);
    }
}

// Submit a solution
async function submitSolution(problemId) {
    const solutionCode = document.getElementById('solution-code').value;
    if (!solutionCode) {
        alert('Please write a solution before submitting');
        return;
    }

    try {
        const result = await apiRequest('/api/solutions', 'POST', {
            problem_id: problemId,
            code: solutionCode
        });
        alert(result.message || 'Solution submitted successfully');
    } catch (error) {
        console.error('Error submitting solution:', error);
        alert('Failed to submit solution. Please try again.');
    }
}

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    fetchProblems();
});