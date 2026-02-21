// Path: static/js/app.js
// Purpose: Frontend JavaScript for handling API calls and dynamic interactions.
// Layer: frontend

// API Base URL
const API_BASE_URL = "/api";

// Utility function for making API calls
async function apiCall(endpoint, method = "GET", data = null) {
    const headers = { "Content-Type": "application/json" };
    const options = { method, headers };

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        if (!response.ok) {
            throw new Error(`API call failed: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Error during API call:", error);
        throw error;
    }
}

// Function to fetch and display problems in the library
async function loadProblems() {
    try {
        const problems = await apiCall("/problems");
        const problemList = document.getElementById("problem-list");
        problemList.innerHTML = ""; // Clear current list

        problems.forEach(problem => {
            const listItem = document.createElement("li");
            listItem.textContent = `${problem.id}. ${problem.title}`;
            listItem.dataset.problemId = problem.id;
            problemList.appendChild(listItem);
        });
    } catch (error) {
        console.error("Failed to load problems:", error);
    }
}

// Function to submit a solution
async function submitSolution(problemId, solutionCode) {
    try {
        const result = await apiCall(`/problems/${problemId}/submit`, "POST", { code: solutionCode });
        alert(`Submission Result: ${result.message}`);
        return result;
    } catch (error) {
        console.error("Failed to submit solution:", error);
    }
}

// Event listener for problem list click
document.getElementById("problem-list").addEventListener("click", async (event) => {
    const problemId = event.target.dataset.problemId;
    if (problemId) {
        const solutionCode = prompt("Enter your solution code:");
        if (solutionCode) {
            await submitSolution(problemId, solutionCode);
        }
    }
});

// Load problems on page load
window.addEventListener("DOMContentLoaded", loadProblems);