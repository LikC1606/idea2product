// static/js/app.js

// Purpose: This file handles frontend functionalities such as interacting with the backend API, managing UI components, and rendering dynamic content.

// Constants for API endpoints
const BASE_API_URL = "/api";
const PROBLEMS_API = `${BASE_API_URL}/problems`;
const SOLUTIONS_API = `${BASE_API_URL}/solutions`;
const USERS_API = `${BASE_API_URL}/users`;

// Utility function to make API requests
async function makeApiRequest(url, method = 'GET', data = null) {
  const options = {
    method: method,
    headers: {
      'Content-Type': 'application/json',
    },
  };

  if (data) {
    options.body = JSON.stringify(data);
  }

  try {
    const response = await fetch(url, options);
    if (!response.ok) {
      throw new Error(`API request failed with status ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error:", error);
    return null;
  }
}

// Fetch and render problems
async function fetchProblems() {
  const problemsContainer = document.getElementById('problems-container');
  problemsContainer.innerHTML = 'Loading...';

  const problems = await makeApiRequest(PROBLEMS_API);
  if (problems) {
    problemsContainer.innerHTML = problems.map(problem => `
      <div class="problem-item">
        <h3>${problem.title}</h3>
        <p>${problem.description}</p>
        <button onclick="viewProblem(${problem.id})">View</button>
      </div>
    `).join('');
  } else {
    problemsContainer.innerHTML = 'Failed to load problems.';
  }
}

// View problem details
async function viewProblem(problemId) {
  const problemDetailsContainer = document.getElementById('problem-details-container');
  problemDetailsContainer.innerHTML = 'Loading...';

  const problem = await makeApiRequest(`${PROBLEMS_API}/${problemId}`);
  if (problem) {
    problemDetailsContainer.innerHTML = `
      <h2>${problem.title}</h2>
      <p>${problem.description}</p>
      <button onclick="submitSolution(${problem.id})">Submit Solution</button>
    `;
  } else {
    problemDetailsContainer.innerHTML = 'Failed to load problem details.';
  }
}

// Submit solution
async function submitSolution(problemId) {
  const solutionCode = prompt("Enter your solution code:");
  const solutionData = {
    problem_id: problemId,
    code: solutionCode,
    language: "JavaScript", // Example language, can be dynamic
  };

  const result = await makeApiRequest(SOLUTIONS_API, 'POST', solutionData);
  if (result) {
    alert("Solution submitted successfully!");
  } else {
    alert("Failed to submit solution.");
  }
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
  fetchProblems();
});