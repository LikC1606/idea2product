// static/js/app.js

// Purpose: Frontend logic for the ACM Problem-Solving Platform
// Layer: frontend

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
  console.log('ACM Problem-Solving Platform loaded successfully.');

  // Example: Navigation handler
  const navLinks = document.querySelectorAll('.nav-link');
  navLinks.forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      const target = e.target.getAttribute('href');
      if (target) {
        navigateTo(target);
      }
    });
  });
});

// Function to handle navigation
function navigateTo(target) {
  console.log(`Navigating to ${target}`);
  // Implement navigation logic
}

// Example: Form submission handler
const submissionForms = document.querySelectorAll('.submission-form');
submissionForms.forEach(form => {
  form.addEventListener('submit', e => {
    e.preventDefault();
    const formData = new FormData(e.target);
    console.log('Form submitted:', formData);

    // Example: Send data to server (replace with actual implementation)
    fetch('/submit', {
      method: 'POST',
      body: formData,
    })
      .then(response => response.json())
      .then(data => {
        console.log('Response:', data);
        alert('Submission successful!');
      })
      .catch(error => {
        console.error('Error:', error);
        alert('Submission failed!');
      });
  });
});

// Example: Dynamic element update
function updateLeaderboard(data) {
  const leaderboard = document.querySelector('#leaderboard');
  leaderboard.innerHTML = '';

  data.forEach(user => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${user.rank}</td>
      <td>${user.username}</td>
      <td>${user.score}</td>
    `;
    leaderboard.appendChild(row);
  });
}

// Example usage: Update leaderboard with mock data
updateLeaderboard([
  { rank: 1, username: 'Alice', score: 100 },
  { rank: 2, username: 'Bob', score: 90 },
  { rank: 3, username: 'Carol', score: 80 },
]);

// Export (if required for linking in HTML templates)
export { navigateTo, updateLeaderboard };