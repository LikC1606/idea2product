// static/js/app.js

// Frontend JavaScript for ACM Problem-Solving Platform

// DOM Elements
const problemListElement = document.getElementById("problem-list");
const leaderboardElement = document.getElementById("leaderboard");
const profileElement = document.getElementById("user-profile");
const submitButton = document.getElementById("submit-button");
const codeEditor = document.getElementById("code-editor");
const hintElement = document.getElementById("hints");

// Fetch Problems and Display in Problem Repository
async function fetchProblems() {
    try {
        const response = await fetch("/problems");
        const problems = await response.json();
        renderProblems(problems);
    } catch (error) {
        console.error("Error fetching problems:", error);
    }
}

function renderProblems(problems) {
    problemListElement.innerHTML = problems
        .map((problem) => `<li>${problem.title}</li>`)
        .join("");
}

// Submit Code for Evaluation
async function submitCode() {
    const code = codeEditor.value;
    const problemId = document.getElementById("problem-id").value;

    try {
        const response = await fetch(`/submit/${problemId}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ code })
        });

        const result = await response.json();
        displaySubmissionResult(result);
    } catch (error) {
        console.error("Error submitting code:", error);
    }
}

function displaySubmissionResult(result) {
    const resultElement = document.getElementById("submission-result");
    resultElement.textContent = result.message;
    resultElement.style.color = result.success ? "green" : "red";
}

// Fetch Leaderboard
async function fetchLeaderboard() {
    try {
        const response = await fetch("/leaderboard");
        const leaderboard = await response.json();
        renderLeaderboard(leaderboard);
    } catch (error) {
        console.error("Error fetching leaderboard:", error);
    }
}

function renderLeaderboard(leaderboard) {
    leaderboardElement.innerHTML = leaderboard
        .map((entry) => `<li>${entry.username}: ${entry.score}</li>`)
        .join("");
}

// Fetch User Profile
async function fetchUserProfile(userId) {
    try {
        const response = await fetch(`/users/${userId}`);
        const profile = await response.json();
        renderUserProfile(profile);
    } catch (error) {
        console.error("Error fetching user profile:", error);
    }
}

function renderUserProfile(profile) {
    profileElement.innerHTML = `
        <h2>${profile.name}</h2>
        <p>Score: ${profile.score}</p>
        <p>Problems Solved: ${profile.problemsSolved}</p>
    `;
}

// Fetch Hints for a Problem
async function fetchHints(problemId) {
    try {
        const response = await fetch(`/hints/${problemId}`);
        const hints = await response.json();
        renderHints(hints);
    } catch (error) {
        console.error("Error fetching hints:", error);
    }
}

function renderHints(hints) {
    hintElement.innerHTML = hints
        .map((hint) => `<p>${hint}</p>`)
        .join("");
}

// Event Listeners
submitButton.addEventListener("click", submitCode);

// Initial Data Fetching
fetchProblems();
fetchLeaderboard();