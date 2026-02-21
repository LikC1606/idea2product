// Module: static.js.app
// Layer: frontend
// Database: none

// This file handles frontend functionalities for the ACM Problem-Solving Platform.

// Event Listeners
document.addEventListener("DOMContentLoaded", () => {
  console.log("Frontend app.js loaded successfully!");

  // Example: Add event listeners for buttons
  const submitButton = document.querySelector("#submit-button");
  if (submitButton) {
    submitButton.addEventListener("click", handleSubmit);
  }

  const problemLinks = document.querySelectorAll(".problem-link");
  problemLinks.forEach((link) => {
    link.addEventListener("click", handleProblemClick);
  });
});

// Functions
function handleSubmit(event) {
  event.preventDefault();
  const codeEditor = document.querySelector("#code-editor");
  const problemId = document.querySelector("#problem-id").value;

  if (codeEditor && problemId) {
    const code = codeEditor.value;
    console.log(`Submitting code for problem ${problemId}:`, code);

    // Submit the code (AJAX or Fetch API can be used for backend communication)
    // Example:
    // fetch('/submit', { method: 'POST', body: JSON.stringify({ code, problemId }) })
    //   .then(response => response.json())
    //   .then(data => console.log(data))
    //   .catch(error => console.error('Error:', error));
  } else {
    alert("Please ensure all fields are filled out.");
  }
}

function handleProblemClick(event) {
  event.preventDefault();
  const problemId = event.target.dataset.problemId;

  if (problemId) {
    console.log(`Navigating to problem ${problemId}`);
    // Redirect to problem page
    window.location.href = `/problems/${problemId}`;
  }
}

// Utility Functions
function showNotification(message, type = "info") {
  const notification = document.createElement("div");
  notification.className = `notification notification-${type}`;
  notification.textContent = message;

  document.body.appendChild(notification);

  setTimeout(() => {
    document.body.removeChild(notification);
  }, 3000);
}

// Must Export: (none)