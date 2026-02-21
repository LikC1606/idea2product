// scripts.js

// Function to fetch and display problems
async function fetchProblems() {
    try {
        const response = await fetch('/problems');
        if (response.ok) {
            const problems = await response.json();
            displayProblems(problems);
        } else {
            console.error('Failed to fetch problems:', response.status);
        }
    } catch (error) {
        console.error('Error while fetching problems:', error);
    }
}

// Function to display problems in the UI
function displayProblems(problems) {
    const problemList = document.getElementById('problem-list');
    problemList.innerHTML = '';
    problems.forEach((problem) => {
        const listItem = document.createElement('li');
        listItem.textContent = `${problem.title} - ${problem.description}`;
        listItem.onclick = () => fetchProblemDetails(problem.id);
        problemList.appendChild(listItem);
    });
}

// Function to fetch and display problem details
async function fetchProblemDetails(problemId) {
    try {
        const response = await fetch(`/problems/${problemId}`);
        if (response.ok) {
            const problem = await response.json();
            displayProblemDetails(problem);
        } else {
            console.error('Failed to fetch problem details:', response.status);
        }
    } catch (error) {
        console.error('Error while fetching problem details:', error);
    }
}

// Function to display problem details in the UI
function displayProblemDetails(problem) {
    const problemDetails = document.getElementById('problem-details');
    problemDetails.innerHTML = `
        <h3>${problem.title}</h3>
        <p>${problem.description}</p>
    `;
}

// Function to add a new problem
async function addProblem(title, description) {
    try {
        const response = await fetch('/problems', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, description }),
        });
        if (response.ok) {
            fetchProblems(); // Refresh the problem list
        } else {
            console.error('Failed to add problem:', response.status);
        }
    } catch (error) {
        console.error('Error while adding problem:', error);
    }
}

// Function to delete a problem
async function deleteProblem(problemId) {
    try {
        const response = await fetch(`/problems/${problemId}`, { method: 'DELETE' });
        if (response.ok) {
            fetchProblems(); // Refresh the problem list
        } else {
            console.error('Failed to delete problem:', response.status);
        }
    } catch (error) {
        console.error('Error while deleting problem:', error);
    }
}

// Event listener for adding problems
document.getElementById('add-problem-form').addEventListener('submit', (event) => {
    event.preventDefault();
    const title = document.getElementById('problem-title').value;
    const description = document.getElementById('problem-description').value;
    addProblem(title, description);
    event.target.reset();
});

// Initial fetch of problems
fetchProblems();