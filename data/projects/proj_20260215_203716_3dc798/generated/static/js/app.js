// static/js/app.js

// Function to fetch all problems and display them on the frontend
async function fetchProblems() {
    try {
        const response = await fetch('/problems');
        const problems = await response.json();

        const problemList = document.getElementById('problem-list');
        problemList.innerHTML = '';

        problems.forEach(problem => {
            const problemItem = document.createElement('li');
            problemItem.textContent = `${problem.title} - Difficulty: ${problem.difficulty}`;
            problemItem.onclick = () => viewProblem(problem.id);
            problemList.appendChild(problemItem);
        });
    } catch (error) {
        console.error('Error fetching problems:', error);
    }
}

// Function to fetch and display a single problem
async function viewProblem(problemId) {
    try {
        const response = await fetch(`/problems/${problemId}`);
        const problem = await response.json();

        const problemDetail = document.getElementById('problem-detail');
        problemDetail.innerHTML = `
            <h2>${problem.title}</h2>
            <p>${problem.description}</p>
            <p>Difficulty: ${problem.difficulty}</p>
            <button onclick="submitSolution(${problem.id})">Submit Solution</button>
        `;
    } catch (error) {
        console.error('Error fetching problem:', error);
    }
}

// Function to submit a solution for a problem
async function submitSolution(problemId) {
    const code = prompt('Enter your solution code:');
    if (!code) return;

    try {
        const response = await fetch('/solutions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                problem_id: problemId,
                user_id: 1, // Replace with actual user ID
                code: code,
            }),
        });

        if (response.ok) {
            alert('Solution submitted successfully!');
        } else {
            const errorData = await response.json();
            alert(`Error submitting solution: ${errorData.message}`);
        }
    } catch (error) {
        console.error('Error submitting solution:', error);
    }
}

// Fetch problems on page load
document.addEventListener('DOMContentLoaded', fetchProblems);