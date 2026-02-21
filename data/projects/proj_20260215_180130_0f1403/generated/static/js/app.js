// Module: app_js
// Layer: frontend
// Purpose: Frontend JavaScript for ACM Problem-Solving Platform

// DOM Elements
const problemList = document.getElementById('problem-list');
const userProfile = document.getElementById('user-profile');
const submitButton = document.getElementById('submit-button');

// Event Listeners
if (problemList) {
  problemList.addEventListener('click', (e) => {
    const target = e.target;
    if (target.classList.contains('problem-link')) {
      const problemId = target.getAttribute('data-problem-id');
      loadProblem(problemId);
    }
  });
}

if (userProfile) {
  userProfile.addEventListener('click', (e) => {
    const target = e.target;
    if (target.id === 'edit-profile') {
      editProfile();
    }
  });
}

if (submitButton) {
  submitButton.addEventListener('click', (e) => {
    e.preventDefault();
    submitSolution();
  });
}

// Functions
function loadProblem(problemId) {
  fetch(`/problem/${problemId}`)
    .then((response) => response.json())
    .then((data) => {
      const problemContainer = document.getElementById('problem-container');
      problemContainer.innerHTML = `<h2>${data.title}</h2><p>${data.description}</p>`;
    })
    .catch((error) => console.error('Error loading problem:', error));
}

function editProfile() {
  alert('Profile editing is not yet implemented.');
}

function submitSolution() {
  const solutionCode = document.getElementById('code-editor').value;
  const problemId = document.getElementById('problem-id').value;

  fetch(`/solution/submit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ problemId, code: solutionCode }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        alert('Solution submitted successfully!');
      } else {
        alert(`Error: ${data.message}`);
      }
    })
    .catch((error) => console.error('Error submitting solution:', error));
}

// Export (if applicable)