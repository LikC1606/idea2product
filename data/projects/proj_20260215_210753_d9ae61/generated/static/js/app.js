// static/js/app.js

// Function to fetch problem data from the server
async function fetchProblemData(problemId) {
    try {
        const response = await fetch(`/api/problems/${problemId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch problem data');
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching problem data:', error);
    }
}

// Function to submit a solution for evaluation
async function submitSolution(problemId, solutionCode) {
    try {
        const response = await fetch(`/api/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                problem_id: problemId,
                solution_code: solutionCode
            })
        });

        if (!response.ok) {
            throw new Error('Failed to submit solution');
        }

        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Error submitting solution:', error);
    }
}

// Function to update leaderboard data
async function fetchLeaderboardData() {
    try {
        const response = await fetch(`/api/leaderboard`);
        if (!response.ok) {
            throw new Error('Failed to fetch leaderboard data');
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching leaderboard data:', error);
    }
}

// Function to display problem details on the frontend
function displayProblem(problemData) {
    const problemContainer = document.getElementById('problem-container');
    if (!problemContainer) return;

    problemContainer.innerHTML = `
        <h2>${problemData.title}</h2>
        <p>${problemData.description}</p>
        <pre>${problemData.input_format}</pre>
        <pre>${problemData.output_format}</pre>
    `;
}

// Function to handle solution submission
async function handleSubmit(event) {
    event.preventDefault();

    const problemId = document.getElementById('problem-id').value;
    const solutionCode = document.getElementById('solution-code').value;

    const result = await submitSolution(problemId, solutionCode);

    if (result) {
        const resultContainer = document.getElementById('result-container');
        resultContainer.textContent = `Result: ${result.message}`;
    }
}

// Initialize event listeners after DOM content is loaded
document.addEventListener('DOMContentLoaded', () => {
    const submitButton = document.getElementById('submit-button');
    if (submitButton) {
        submitButton.addEventListener('click', handleSubmit);
    }

    const problemId = document.getElementById('problem-id')?.value;
    if (problemId) {
        fetchProblemData(problemId).then(displayProblem);
    }
});