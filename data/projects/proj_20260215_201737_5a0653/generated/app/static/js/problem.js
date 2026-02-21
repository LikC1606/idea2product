// Path: app/static/js/problem.js
// Purpose: Interface Layer for Problem Module in ACM Problem-Solving Platform

// Function to fetch problem data from the server and populate the problem display
async function fetchProblem(problemId) {
    try {
        const response = await fetch(`/api/problems/${problemId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch problem');
        }
        const problemData = await response.json();
        displayProblem(problemData);
    } catch (error) {
        console.error('Error fetching problem:', error);
        alert('Unable to load problem. Please try again.');
    }
}

// Function to render problem data on the page
function displayProblem(problemData) {
    const problemTitleElement = document.getElementById('problem-title');
    const problemDescriptionElement = document.getElementById('problem-description');
    const problemInputElement = document.getElementById('problem-input');
    const problemOutputElement = document.getElementById('problem-output');

    problemTitleElement.textContent = problemData.title;
    problemDescriptionElement.textContent = problemData.description;
    problemInputElement.textContent = `Input: ${problemData.input}`;
    problemOutputElement.textContent = `Output: ${problemData.output}`;
}

// Function to submit code and evaluate the solution
async function submitCode(problemId) {
    const codeInputElement = document.getElementById('code-input');
    const code = codeInputElement.value;

    try {
        const response = await fetch(`/api/problems/${problemId}/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ code }),
        });

        if (!response.ok) {
            throw new Error('Failed to submit code');
        }

        const result = await response.json();
        displaySubmissionResult(result);
    } catch (error) {
        console.error('Error submitting code:', error);
        alert('Unable to submit code. Please try again.');
    }
}

// Function to display the result of the code submission
function displaySubmissionResult(result) {
    const resultElement = document.getElementById('submission-result');
    if (result.success) {
        resultElement.textContent = `Success! Your solution is correct. Time: ${result.time}s, Memory: ${result.memory}MB`;
        resultElement.style.color = 'green';
    } else {
        resultElement.textContent = `Failed: ${result.error}`;
        resultElement.style.color = 'red';
    }
}

// Attach event listeners
document.addEventListener('DOMContentLoaded', () => {
    const submitButton = document.getElementById('submit-btn');
    const problemId = document.getElementById('problem-id').value;

    // Load the problem details when the page is loaded
    fetchProblem(problemId);

    // Attach the submit code functionality to the button
    submitButton.addEventListener('click', () => submitCode(problemId));
});