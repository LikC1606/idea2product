// Module: static.js.app
// Layer: frontend
// Database: none

// This file handles the frontend logic for the ACM Problem-Solving Platform.

// Event listener for document ready
document.addEventListener("DOMContentLoaded", function () {
  console.log("Frontend logic initialized.");

  // Example: Handle form submissions
  const submissionForm = document.getElementById("submissionForm");
  if (submissionForm) {
    submissionForm.addEventListener("submit", function (e) {
      e.preventDefault();
      const formData = new FormData(submissionForm);
      const problemId = formData.get("problemId");
      const solutionCode = formData.get("solutionCode");

      // Example: Display loading spinner
      const loadingSpinner = document.getElementById("loadingSpinner");
      if (loadingSpinner) {
        loadingSpinner.style.display = "block";
      }

      // Example: Send solution to backend (AJAX or Fetch API)
      fetch(`/submit/${problemId}`, {
        method: "POST",
        body: JSON.stringify({ solution: solutionCode }),
        headers: {
          "Content-Type": "application/json",
        },
      })
        .then((response) => response.json())
        .then((data) => {
          // Hide loading spinner
          if (loadingSpinner) {
            loadingSpinner.style.display = "none";
          }

          // Process response from backend
          if (data.success) {
            alert("Solution submitted successfully!");
          } else {
            alert("Submission failed: " + data.error);
          }
        })
        .catch((error) => {
          // Hide loading spinner
          if (loadingSpinner) {
            loadingSpinner.style.display = "none";
          }
          alert("An error occurred: " + error.message);
        });
    });
  }

  // Example: Toggle visibility of hints
  const hintButton = document.getElementById("showHintButton");
  const hintContent = document.getElementById("hintContent");
  if (hintButton && hintContent) {
    hintButton.addEventListener("click", function () {
      if (hintContent.style.display === "none" || hintContent.style.display === "") {
        hintContent.style.display = "block";
        hintButton.textContent = "Hide Hint";
      } else {
        hintContent.style.display = "none";
        hintButton.textContent = "Show Hint";
      }
    });
  }
});