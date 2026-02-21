// static/js/app.js

document.addEventListener("DOMContentLoaded", function () {
    // Initialize event listeners
    initializeEventListeners();
});

function initializeEventListeners() {
    // Add event listeners for problem library
    const problemLinks = document.querySelectorAll('.problem-link');
    problemLinks.forEach(link => {
        link.addEventListener('click', function (event) {
            event.preventDefault();
            const problemId = this.dataset.problemId;
            fetchProblemDetails(problemId);
        });
    });

    // Add event listener for code submission
    const submitButton = document.getElementById('submit-code-button');
    if (submitButton) {
        submitButton.addEventListener('click', function () {
            submitCode();
        });
    }
}

function fetchProblemDetails(problemId) {
    fetch(`/problem/${problemId}`)
        .then(response => response.json())
        .then(data => {
            displayProblemDetails(data);
        })
        .catch(error => {
            console.error('Error fetching problem details:', error);
        });
}

function displayProblemDetails(problemData) {
    const problemTitle = document.getElementById('problem-title');
    const problemDescription = document.getElementById('problem-description');
    if (problemTitle && problemDescription) {
        problemTitle.textContent = problemData.title;
        problemDescription.textContent = problemData.description;
    }
}

function submitCode() {
    const codeInput = document.getElementById('code-input');
    const problemId = document.getElementById('problem-id').value;

    if (!codeInput || !problemId) {
        console.error('Code input or problem ID is missing.');
        return;
    }

    const code = codeInput.value;
    const requestData = {
        problem_id: problemId,
        code: code
    };

    fetch('/submit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Code submitted successfully!');
            } else {
                alert('Error submitting code: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error submitting code:', error);
        });
}