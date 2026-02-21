// Define constants for DOM elements
const problemContainer = document.getElementById('problem-container');
const userProfile = document.getElementById('user-profile');
const solutionForm = document.getElementById('solution-form');
const leaderboard = document.getElementById('leaderboard');

// Utility function to fetch data from the backend
async function fetchData(url) {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch data from ${url}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching data:', error);
  }
}

// Render problems in the problem library
async function loadProblems() {
  const problems = await fetchData('/api/problems');
  if (problems) {
    problemContainer.innerHTML = problems
      .map(
        (problem) => `
        <div class="problem">
          <h3>${problem.title}</h3>
          <p>${problem.description}</p>
          <button onclick="viewProblem(${problem.id})">View Problem</button>
        </div>
      `
      )
      .join('');
  }
}

// View problem details
async function viewProblem(problemId) {
  const problem = await fetchData(`/api/problems/${problemId}`);
  if (problem) {
    alert(`Title: ${problem.title}\nDescription: ${problem.description}\nHint: ${problem.hint}`);
  }
}

// Render user profile
async function loadUserProfile(userId) {
  const user = await fetchData(`/api/users/${userId}`);
  if (user) {
    userProfile.innerHTML = `
      <h2>${user.username}</h2>
      <p>Rank: ${user.rank}</p>
      <p>Problems Solved: ${user.problemsSolved}</p>
    `;
  }
}

// Submit solution
solutionForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const formData = new FormData(solutionForm);
  const solutionData = {
    problemId: formData.get('problemId'),
    code: formData.get('code'),
  };

  try {
    const response = await fetch('/api/solutions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(solutionData),
    });

    if (response.ok) {
      const result = await response.json();
      alert(`Submission Result: ${result.status}`);
    } else {
      throw new Error('Failed to submit solution');
    }
  } catch (error) {
    console.error('Error submitting solution:', error);
  }
});

// Load leaderboard
async function loadLeaderboard() {
  const leaderboardData = await fetchData('/api/leaderboard');
  if (leaderboardData) {
    leaderboard.innerHTML = leaderboardData
      .map(
        (user) => `
        <div class="leaderboard-entry">
          <span>${user.username}</span>
          <span>Rank: ${user.rank}</span>
          <span>Problems Solved: ${user.problemsSolved}</span>
        </div>
      `
      )
      .join('');
  }
}

// Initial Load
document.addEventListener('DOMContentLoaded', () => {
  loadProblems();
  loadLeaderboard();
});