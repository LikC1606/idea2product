// Path: app/static/js/scripts.js
// Purpose: Interface Layer for ACM Problem-Solving Platform

// Event listener for form submissions (e.g., problem submission)
document.addEventListener('submit', function (event) {
    event.preventDefault(); // Prevent default form submission

    const form = event.target;
    const formData = new FormData(form);
    const action = form.getAttribute('action');
    const method = form.getAttribute('method') || 'POST';

    // Submit data using Fetch API
    fetch(action, {
        method: method,
        body: formData,
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error('Network response was not ok' + response.statusText);
            }
            return response.json();
        })
        .then((data) => {
            // Handle successful response
            if (data.success) {
                alert('Submission Successful!');
                // Perform additional actions (e.g., redirect, update UI)
            } else {
                alert('Submission Failed: ' + data.message);
            }
        })
        .catch((error) => {
            // Handle errors
            console.error('There was a problem with the fetch operation:', error);
            alert('An error occurred. Please try again.');
        });
});

// Dynamic leaderboard update
function updateLeaderboard() {
    fetch('/leaderboard')
        .then((response) => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then((data) => {
            const leaderboard = document.getElementById('leaderboard');
            leaderboard.innerHTML = ''; // Clear existing leaderboard

            data.users.forEach((user, index) => {
                const userRow = document.createElement('div');
                userRow.classList.add('leaderboard-row');
                userRow.innerHTML = `
                    <span class="rank">${index + 1}</span>
                    <span class="name">${user.name}</span>
                    <span class="score">${user.score}</span>
                `;
                leaderboard.appendChild(userRow);
            });
        })
        .catch((error) => {
            console.error('Error fetching leaderboard:', error);
        });
}

// Periodic leaderboard refresh
setInterval(updateLeaderboard, 60000); // Refresh every 60 seconds

// Hint button functionality
document.addEventListener('click', function (event) {
    if (event.target && event.target.classList.contains('hint-button')) {
        const problemId = event.target.dataset.problemId;

        fetch(`/problems/${problemId}/hints`)
            .then((response) => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then((data) => {
                if (data.success) {
                    alert('Hint: ' + data.hint);
                } else {
                    alert('No hints available for this problem.');
                }
            })
            .catch((error) => {
                console.error('Error fetching hint:', error);
                alert('An error occurred while fetching the hint.');
            });
    }
});

// Code evaluation result display
function displayEvaluationResult(result) {
    const resultContainer = document.getElementById('evaluation-result');
    resultContainer.innerHTML = `
        <h3>Evaluation Result:</h3>
        <p>Status: ${result.status}</p>
        <p>Message: ${result.message}</p>
    `;
}

// Code submission handler
document.addEventListener('click', function (event) {
    if (event.target && event.target.id === 'submit-code-button') {
        const codeInput = document.getElementById('code-input').value;
        const problemId = event.target.dataset.problemId;

        fetch(`/problems/${problemId}/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ code: codeInput }),
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then((data) => {
                if (data.success) {
                    displayEvaluationResult(data.result);
                } else {
                    alert('Code submission failed: ' + data.message);
                }
            })
            .catch((error) => {
                console.error('Error submitting code:', error);
                alert('An error occurred while submitting the code.');
            });
    }
});