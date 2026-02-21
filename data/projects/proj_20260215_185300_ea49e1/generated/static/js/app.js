// Module: static.js.app
// Layer: frontend

// Purpose: This file serves as the main JavaScript logic for the frontend of the ACM Problem-Solving Platform.
// Interface Specifications: No database interaction. Purely frontend logic.

// No imports required

// Example functionality to handle user interactions and dynamic behavior on the frontend.
document.addEventListener("DOMContentLoaded", () => {
    // DOM elements
    const problemList = document.getElementById("problem-list");
    const submitButton = document.getElementById("submit-button");
    const userProfile = document.getElementById("user-profile");

    // Add event listener for problem selection
    if (problemList) {
        problemList.addEventListener("click", (event) => {
            const target = event.target;
            if (target && target.classList.contains("problem-item")) {
                const problemId = target.dataset.problemId;
                loadProblemDetails(problemId);
            }
        });
    }

    // Add event listener for submission
    if (submitButton) {
        submitButton.addEventListener("click", () => {
            const codeInput = document.getElementById("code-input");
            const problemId = document.getElementById("problem-id").value;

            if (codeInput && problemId) {
                submitSolution(problemId, codeInput.value);
            }
        });
    }

    // Add event listener for user profile interactions
    if (userProfile) {
        userProfile.addEventListener("click", () => {
            loadUserProfile();
        });
    }
});

// Function to load problem details dynamically
function loadProblemDetails(problemId) {
    fetch(`/problems/${problemId}`)
        .then((response) => response.json())
        .then((data) => {
            const problemDetails = document.getElementById("problem-details");
            if (problemDetails) {
                problemDetails.innerHTML = `
                    <h2>${data.title}</h2>
                    <p>${data.description}</p>
                `;
            }
        })
        .catch((error) => console.error("Error loading problem details:", error));
}

// Function to submit user solution
function submitSolution(problemId, code) {
    fetch(`/solutions/submit`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            problem_id: problemId,
            code: code,
        }),
    })
        .then((response) => response.json())
        .then((data) => {
            alert(`Submission Result: ${data.result}`);
        })
        .catch((error) => console.error("Error submitting solution:", error));
}

// Function to load the user's profile
function loadUserProfile() {
    fetch(`/user/profile`)
        .then((response) => response.json())
        .then((data) => {
            const profileSection = document.getElementById("profile-section");
            if (profileSection) {
                profileSection.innerHTML = `
                    <h2>${data.username}</h2>
                    <p>Problems Solved: ${data.problems_solved}</p>
                    <p>Rank: ${data.rank}</p>
                `;
            }
        })
        .catch((error) => console.error("Error loading user profile:", error));
}

// Must Export: Nothing as this is a frontend file, all logic is loaded in the browser.