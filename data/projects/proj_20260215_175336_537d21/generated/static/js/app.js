// Module: app_js
// Layer: frontend
// Purpose: Frontend JavaScript for ACM Problem-Solving Platform

// Ensure the DOM is fully loaded before executing any code
document.addEventListener("DOMContentLoaded", function () {
    console.log("Frontend JavaScript loaded.");

    // Handle navigation bar active state
    const navLinks = document.querySelectorAll(".nav-link");
    navLinks.forEach(link => {
        link.addEventListener("click", function () {
            navLinks.forEach(nav => nav.classList.remove("active"));
            this.classList.add("active");
        });
    });

    // Handle problem selection
    const problemListItems = document.querySelectorAll(".problem-item");
    problemListItems.forEach(item => {
        item.addEventListener("click", function () {
            const problemId = this.getAttribute("data-problem-id");
            window.location.href = `/problem/${problemId}`;
        });
    });

    // Handle submission form
    const submissionForm = document.querySelector("#submission-form");
    if (submissionForm) {
        submissionForm.addEventListener("submit", function (event) {
            event.preventDefault();

            const formData = new FormData(submissionForm);
            const code = formData.get("code");
            const problemId = formData.get("problem-id");

            if (!code.trim()) {
                alert("Code cannot be empty!");
                return;
            }

            fetch(`/submit/${problemId}`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ code })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert("Submission Successful!");
                        window.location.reload();
                    } else {
                        alert(`Submission Failed: ${data.error}`);
                    }
                })
                .catch(error => console.error("Error:", error));
        });
    }
});