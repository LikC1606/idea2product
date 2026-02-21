// File: app/static/js/problem.js
// Purpose: Interface Layer for Problem Page in ACM Problem-Solving Platform

// Initialize global variables
let problemId = null;
let editor = null;

// Function to initialize the code editor (using CodeMirror or similar library)
function initializeEditor() {
    editor = CodeMirror.fromTextArea(document.getElementById('code-editor'), {
        mode: 'python',
        theme: 'monokai',
        lineNumbers: true,
        indentUnit: 4,
        indentWithTabs: true,
    });
}

// Function to fetch problem details
async function fetchProblemDetails(id) {
    try {
        const response = await fetch(`/api/problems/${id}`);
        if (!response.ok) {
            throw new Error(`Error fetching problem details: ${response.statusText}`);
        }
        const problem = await response.json();
        displayProblemDetails(problem);
    } catch (error) {
        console.error(error);
        alert('Could not fetch problem details. Please try again later.');
    }
}

// Function to display problem details on the page
function displayProblemDetails(problem) {
    document.getElementById('problem-title').innerText = problem.title;
    document.getElementById('problem-description').innerText = problem.description;
    document.getElementById('problem-input-format').innerText = problem.input_format;
    document.getElementById('problem-output-format').innerText = problem.output_format;
    document.getElementById('problem-sample-input').innerText = problem.sample_input;
    document.getElementById('problem-sample-output').innerText = problem.sample_output;
}

// Function to submit code for evaluation
async function submitCode() {
    const code = editor.getValue();
    if (!code.trim()) {
        alert('Please write some code before submitting.');
        return;
    }

    try {
        const response = await fetch(`/api/problems/${problemId}/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ code }),
        });

        if (!response.ok) {
            throw new Error(`Error submitting code: ${response.statusText}`);
        }

        const result = await response.json();
        displaySubmissionResult(result);
    } catch (error) {
        console.error(error);
        alert('Code submission failed. Please try again later.');
    }
}

// Function to display submission results
function displaySubmissionResult(result) {
    const resultContainer = document.getElementById('submission-result');
    resultContainer.innerHTML = `
        <h3>Results:</h3>
        <p>Status: ${result.status}</p>
        <p>Message: ${result.message}</p>
        <p>Execution Time: ${result.execution_time} ms</p>
        <p>Memory Used: ${result.memory_used} KB</p>
    `;
}

// Event listener for submission button
document.getElementById('submit-code-button').addEventListener('click', submitCode);

// Fetch problem details on page load
document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    problemId = urlParams.get('id');
    if (problemId) {
        fetchProblemDetails(problemId);
        initializeEditor();
    } else {
        alert('No problem ID provided. Please go back and select a problem.');
    }
});