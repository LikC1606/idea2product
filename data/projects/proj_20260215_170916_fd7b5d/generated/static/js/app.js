// static/js/app.js
// Frontend JavaScript logic for ACM Problem-Solving Platform

// Function to initialize the application
function initApp() {
  console.log("ACM Problem-Solving Platform initialized.");
}

// Event listener for DOMContentLoaded
document.addEventListener("DOMContentLoaded", function () {
  initApp();
});

// Function to handle problem submission
function handleSubmit() {
  const codeInput = document.getElementById("codeInput").value;
  const problemId = document.getElementById("problemId").value;

  if (!codeInput || !problemId) {
    alert("Please provide both problem ID and code.");
    return;
  }

  const submissionData = {
    problemId: problemId,
    code: codeInput
  };

  fetch("/submit", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(submissionData)
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        alert("Code submitted successfully!");
      } else {
        alert("Submission failed: " + data.message);
      }
    })
    .catch(error => {
      console.error("Error:", error);
      alert("An error occurred while submitting your code.");
    });
}

// Function to load problems
function loadProblems() {
  fetch("/problems")
    .then(response => response.json())
    .then(data => {
      const problemList = document.getElementById("problemList");
      problemList.innerHTML = "";

      data.problems.forEach(problem => {
        const problemItem = document.createElement("li");
        problemItem.textContent = `${problem.id}: ${problem.title}`;
        problemList.appendChild(problemItem);
      });
    })
    .catch(error => {
      console.error("Error loading problems:", error);
    });
}

// Function to display user profile
function loadUserProfile(userId) {
  fetch(`/profile/${userId}`)
    .then(response => response.json())
    .then(data => {
      const userProfile = document.getElementById("userProfile");
      userProfile.innerHTML = `
        <h3>${data.username}</h3>
        <p>Rank: ${data.rank}</p>
        <p>Problems Solved: ${data.problemsSolved}</p>
      `;
    })
    .catch(error => {
      console.error("Error loading user profile:", error);
    });
}

// Export functions (if needed for other scripts)
export { initApp, handleSubmit, loadProblems, loadUserProfile };