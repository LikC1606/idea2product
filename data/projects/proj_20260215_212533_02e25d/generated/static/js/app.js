// static/js/app.js
// Purpose: Frontend JavaScript code for the ACM Problem-Solving Platform

// Function to handle navigation between tabs
function switchTab(tabId) {
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => {
        tab.style.display = 'none';
    });
    document.getElementById(tabId).style.display = 'block';
}

// Function to submit a solution
async function submitSolution(problemId) {
    const codeEditor = document.getElementById('code-editor');
    const solutionCode = codeEditor.value;

    const response = await fetch(`/api/submit/${problemId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code: solutionCode }),
    });

    const result = await response.json();
    if (result.success) {
        alert('Solution submitted successfully!');
        window.location.href = '/leaderboard'; // Redirect to leaderboard
    } else {
        alert(`Error: ${result.error}`);
    }
}

// Function to fetch and display problem details
async function loadProblem(problemId) {
    const response = await fetch(`/api/problem/${problemId}`);
    const data = await response.json();

    if (data.success) {
        document.getElementById('problem-title').innerText = data.problem.title;
        document.getElementById('problem-description').innerText = data.problem.description;
    } else {
        alert(`Error fetching problem details: ${data.error}`);
    }
}

// Function to initialize the code editor
function initializeCodeEditor() {
    const editor = document.getElementById('code-editor');
    editor.value = '// Write your code here...\n';
}

// Event listeners for interactive elements
document.addEventListener('DOMContentLoaded', () => {
    initializeCodeEditor();

    const submitButton = document.getElementById('submit-button');
    if (submitButton) {
        submitButton.addEventListener('click', () => {
            const problemId = submitButton.getAttribute('data-problem-id');
            submitSolution(problemId);
        });
    }

    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            const tabId = link.getAttribute('data-tab');
            switchTab(tabId);
        });
    });
});