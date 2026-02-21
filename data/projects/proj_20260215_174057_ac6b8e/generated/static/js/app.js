// static/js/app.js

// This file handles frontend interactions for the ACM Problem-Solving Platform.

// Event listener for DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize the app
    initializeApp();
});

// Function to initialize the frontend app
function initializeApp() {
    // Load problems into the problem library
    loadProblemLibrary();

    // Handle user profile events
    attachUserProfileListeners();

    // Handle code submission events
    attachCodeSubmissionListeners();

    // Load leaderboard data
    loadLeaderboard();
}

// Function to load problems into the problem library
function loadProblemLibrary() {
    fetch('/problems')
        .then(response => response.json())
        .then(problems => {
            const libraryContainer = document.getElementById('problem-library');
            problems.forEach(problem => {
                const problemCard = createProblemCard(problem);
                libraryContainer.appendChild(problemCard);
            });
        })
        .catch(error => console.error('Error loading problems:', error));
}

// Function to create a problem card element
function createProblemCard(problem) {
    const card = document.createElement('div');
    card.classList.add('problem-card');
    card.innerHTML = `
        <h3>${problem.title}</h3>
        <p>${problem.description}</p>
        <button class="view-problem-button" data-problem-id="${problem.id}">View Problem</button>
    `;
    card.querySelector('.view-problem-button').addEventListener('click', () => {
        viewProblem(problem.id);
    });
    return card;
}

// Function to view a problem
function viewProblem(problemId) {
    fetch(`/problems/${problemId}`)
        .then(response => response.json())
        .then(problem => {
            const problemModal = document.getElementById('problem-modal');
            problemModal.querySelector('.modal-title').innerText = problem.title;
            problemModal.querySelector('.modal-body').innerText = problem.description;
            problemModal.classList.add('show');
        })
        .catch(error => console.error('Error fetching problem:', error));
}

// Function to attach user profile event listeners
function attachUserProfileListeners() {
    const profileButton = document.getElementById('profile-button');
    profileButton.addEventListener('click', () => {
        fetch('/user/profile')
            .then(response => response.json())
            .then(profile => {
                const profileModal = document.getElementById('profile-modal');
                profileModal.querySelector('.modal-title').innerText = profile.name;
                profileModal.querySelector('.modal-body').innerHTML = `
                    <p>Email: ${profile.email}</p>
                    <p>Problems Solved: ${profile.problemsSolved}</p>
                `;
                profileModal.classList.add('show');
            })
            .catch(error => console.error('Error fetching profile:', error));
    });
}

// Function to handle code submission
function attachCodeSubmissionListeners() {
    const submitButton = document.getElementById('submit-code-button');
    submitButton.addEventListener('click', () => {
        const codeInput = document.getElementById('code-input');
        const problemId = document.getElementById('problem-id').value;
        const code = codeInput.value;

        fetch(`/problems/${problemId}/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ code }),
        })
            .then(response => response.json())
            .then(result => {
                const resultContainer = document.getElementById('submission-result');
                resultContainer.innerHTML = `<p>${result.message}</p>`;
            })
            .catch(error => console.error('Error submitting code:', error));
    });
}

// Function to load leaderboard data
function loadLeaderboard() {
    fetch('/leaderboard')
        .then(response => response.json())
        .then(leaderboard => {
            const leaderboardContainer = document.getElementById('leaderboard');
            leaderboard.forEach(entry => {
                const entryElement = document.createElement('div');
                entryElement.classList.add('leaderboard-entry');
                entryElement.innerHTML = `
                    <p>${entry.user}: ${entry.points} points</p>
                `;
                leaderboardContainer.appendChild(entryElement);
            });
        })
        .catch(error => console.error('Error loading leaderboard:', error));
}