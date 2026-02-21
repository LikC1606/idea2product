// static/js/app.js

// Frontend logic for ACM Problem-Solving Platform

// Function to handle problem selection
function loadProblem(problemId) {
    fetch(`/api/problems/${problemId}`)
        .then(response => response.json())
        .then(data => {
            const problemContainer = document.getElementById('problem-container');
            problemContainer.innerHTML = `
                <h2>${data.title}</h2>
                <p>${data.description}</p>
                <pre><code>${data.sample_input}</code></pre>
                <pre><code>${data.sample_output}</code></pre>
            `;
        })
        .catch(error => console.error('Error loading problem:', error));
}

// Function to submit a solution
function submitSolution(problemId, code) {
    fetch(`/api/submit`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            problem_id: problemId,
            code: code,
        }),
    })
        .then(response => response.json())
        .then(data => {
            const resultContainer = document.getElementById('result-container');
            resultContainer.innerHTML = `
                <h3>Submission Result</h3>
                <p>Status: ${data.status}</p>
                <p>Message: ${data.message}</p>
            `;
        })
        .catch(error => console.error('Error submitting solution:', error));
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Load selected problem
    const problemLinks = document.querySelectorAll('.problem-link');
    problemLinks.forEach(link => {
        link.addEventListener('click', event => {
            const problemId = event.target.dataset.problemId;
            loadProblem(problemId);
        });
    });

    // Submit solution form
    const submitForm = document.getElementById('submit-form');
    if (submitForm) {
        submitForm.addEventListener('submit', event => {
            event.preventDefault();
            const problemId = document.getElementById('problem-id').value;
            const code = document.getElementById('code').value;
            submitSolution(problemId, code);
        });
    }
});