// Path: static/js/app.js
// Purpose: Frontend JavaScript
// Layer: frontend

// Define constants for API endpoints
const API_BASE_URL = "/api";

// Utility for making API requests
async function fetchData(url, method = "GET", body = null) {
    const options = {
        method: method,
        headers: {
            "Content-Type": "application/json",
        },
    };
    if (body) {
        options.body = JSON.stringify(body);
    }
    const response = await fetch(url, options);
    if (!response.ok) {
        throw new Error(`HTTP Error: ${response.status}`);
    }
    return response.json();
}

// Load problems into the problem library
async function loadProblems() {
    try {
        const problems = await fetchData(`${API_BASE_URL}/problems`);
        const problemList = document.getElementById("problem-list");
        problemList.innerHTML = ""; // Clear existing list
        problems.forEach((problem) => {
            const listItem = document.createElement("li");
            listItem.textContent = `${problem.title} - ${problem.difficulty}`;
            listItem.dataset.id = problem.id;
            listItem.classList.add("problem-item");
            problemList.appendChild(listItem);
        });
    } catch (error) {
        console.error("Error loading problems:", error);
    }
}

// Submit a solution
async function submitSolution(problemId, code) {
    try {
        const payload = { problemId, code };
        const result = await fetchData(`${API_BASE_URL}/solutions`, "POST", payload);
        alert(`Submission result: ${result.message}`);
    } catch (error) {
        console.error("Error submitting solution:", error);
    }
}

// Attach event listeners for problem selection and code submission
document.addEventListener("DOMContentLoaded", () => {
    const problemList = document.getElementById("problem-list");
    const codeEditor = document.getElementById("code-editor");
    const submitButton = document.getElementById("submit-button");

    problemList.addEventListener("click", (event) => {
        if (event.target.classList.contains("problem-item")) {
            const selectedProblemId = event.target.dataset.id;
            document.getElementById("selected-problem-id").value = selectedProblemId;
            alert(`Problem ${event.target.textContent} selected`);
        }
    });

    submitButton.addEventListener("click", async () => {
        const selectedProblemId = document.getElementById("selected-problem-id").value;
        const code = codeEditor.value;
        if (!selectedProblemId || !code) {
            alert("Please select a problem and write some code!");
            return;
        }
        await submitSolution(selectedProblemId, code);
    });

    // Load problems on page load
    loadProblems();
});