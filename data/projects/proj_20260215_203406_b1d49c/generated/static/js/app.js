// static/js/app.js

// Frontend logic for ACM Problem-Solving Platform
// This script handles user interactions, API calls, and dynamic updates on the frontend.

// Constants for API endpoints
const API_BASE_URL = "/api";

// Utility function to make API requests
async function fetchData(url, method = "GET", data = null) {
    const headers = { "Content-Type": "application/json" };
    const config = { method, headers };

    if (data) {
        config.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, config);
        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Fetch error:", error);
        alert("An error occurred while communicating with the server.");
    }
}

// Function to fetch and display problems
async function loadProblems() {
    const problemsContainer = document.getElementById("problems-list");
    problemsContainer.innerHTML = "<p>Loading problems...</p>";

    const problems = await fetchData(`${API_BASE_URL}/problems`);
    if (problems) {
        problemsContainer.innerHTML = problems.map(problem => `
            <div class="problem-item">
                <h3>${problem.title}</h3>
                <p>${problem.description}</p>
                <button onclick="viewProblem(${problem.id})">View Problem</button>
            </div>
        `).join("");
    }
}

// Function to view a specific problem
async function viewProblem(problemId) {
    const problemContainer = document.getElementById("problem-detail");
    problemContainer.innerHTML = "<p>Loading problem details...</p>";

    const problem = await fetchData(`${API_BASE_URL}/problems/${problemId}`);
    if (problem) {
        problemContainer.innerHTML = `
            <h2>${problem.title}</h2>
            <p>${problem.description}</p>
            <button onclick="submitSolution(${problem.id})">Submit Solution</button>
        `;
    }
}

// Function to submit a solution
async function submitSolution(problemId) {
    const code = prompt("Enter your solution code:");
    if (!code) return;

    const data = { problem_id: problemId, code };
    const result = await fetchData(`${API_BASE_URL}/solutions`, "POST", data);

    if (result) {
        alert("Solution submitted successfully!");
    }
}

// Event listener to load problems on page load
document.addEventListener("DOMContentLoaded", () => {
    loadProblems();
});