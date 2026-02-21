// static/js/app.js

// Purpose: Frontend JavaScript for ACM Problem-Solving Platform
// Layer: Frontend
// Database: sqlalchemy

// Functions to interact with the backend API

// Helper function to make API requests
async function apiRequest(url, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
        },
    };
    if (data) {
        options.body = JSON.stringify(data);
    }

    const response = await fetch(url, options);
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'An error occurred');
    }
    return response.json();
}

// Fetch and render problems
async function fetchProblems() {
    try {
        const problems = await apiRequest('/problems');
        const problemList = document.getElementById('problem-list');
        problemList.innerHTML = '';

        problems.forEach(problem => {
            const listItem = document.createElement('li');
            listItem.textContent = `${problem.title} - Difficulty: ${problem.difficulty}`;
            listItem.addEventListener('click', () => {
                window.location.href = `/problems/${problem.id}`;
            });
            problemList.appendChild(listItem);
        });
    } catch (error) {
        console.error('Error fetching problems:', error);
    }
}

// Fetch and render user profile
async function fetchUserProfile(userId) {
    try {
        const user = await apiRequest(`/users/${userId}`);
        const userProfile = document.getElementById('user-profile');
        userProfile.innerHTML = `
            <h2>${user.name}</h2>
            <p>Email: ${user.email}</p>
        `;
    } catch (error) {
        console.error('Error fetching user profile:', error);
    }
}

// Submit a solution
async function submitSolution(problemId, userId, code) {
    try {
        const solution = {
            problem_id: problemId,
            user_id: userId,
            code,
        };
        const response = await apiRequest('/solutions', 'POST', solution);
        alert('Solution submitted successfully!');
        return response;
    } catch (error) {
        console.error('Error submitting solution:', error);
        alert('Failed to submit solution. Please try again.');
    }
}

// Initialize the page
document.addEventListener('DOMContentLoaded', () => {
    const problemsPage = document.getElementById('problems-page');
    const userProfilePage = document.getElementById('user-profile-page');

    if (problemsPage) {
        fetchProblems();
    } else if (userProfilePage) {
        const userId = userProfilePage.dataset.userId;
        fetchUserProfile(userId);
    }

    const solutionForm = document.getElementById('solution-form');
    if (solutionForm) {
        solutionForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const problemId = document.getElementById('problem-id').value;
            const userId = document.getElementById('user-id').value;
            const code = document.getElementById('code').value;
            await submitSolution(problemId, userId, code);
        });
    }
});