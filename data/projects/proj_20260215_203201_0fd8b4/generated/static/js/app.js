// static/js/app.js

// Purpose: Frontend JavaScript for dynamic interactions on the ACM Problem-Solving Platform
// Layer: Frontend

document.addEventListener("DOMContentLoaded", () => {
    // Fetch and display problem list
    const fetchProblems = async () => {
        try {
            const response = await fetch('/problems');
            const problems = await response.json();
            const problemList = document.getElementById('problem-list');
            problemList.innerHTML = '';
            problems.forEach(problem => {
                const listItem = document.createElement('li');
                listItem.innerHTML = `
                    <a href="/problems/${problem.id}">
                        ${problem.title} - ${problem.difficulty}
                    </a>
                `;
                problemList.appendChild(listItem);
            });
        } catch (error) {
            console.error("Error fetching problems:", error);
        }
    };

    // Submit a solution
    const submitSolution = async (problemId, code, language) => {
        try {
            const response = await fetch(`/solutions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    problem_id: problemId,
                    code: code,
                    language: language,
                }),
            });
            const result = await response.json();
            if (response.ok) {
                alert("Solution submitted successfully!");
            } else {
                alert(`Error: ${result.message}`);
            }
        } catch (error) {
            console.error("Error submitting solution:", error);
        }
    };

    // Event listener for solution submission form
    const solutionForm = document.getElementById('solution-form');
    if (solutionForm) {
        solutionForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const problemId = document.getElementById('problem-id').value;
            const code = document.getElementById('code').value;
            const language = document.getElementById('language').value;
            await submitSolution(problemId, code, language);
        });
    }

    // Fetch problems on page load
    if (document.getElementById('problem-list')) {
        fetchProblems();
    }
});