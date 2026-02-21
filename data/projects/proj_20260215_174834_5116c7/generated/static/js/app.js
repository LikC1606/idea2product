// Path: static/js/app.js
// Purpose: Frontend JavaScript
// Layer: frontend

document.addEventListener('DOMContentLoaded', () => {
  // Base URLs
  const baseURL = '/api';
  const problemEndpoint = `${baseURL}/problems`;
  const userEndpoint = `${baseURL}/users`;
  const solutionEndpoint = `${baseURL}/solutions`;

  // Utility for making API requests
  const apiRequest = async (url, method = 'GET', data = null) => {
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
      throw new Error(`API request failed: ${response.statusText}`);
    }
    return response.json();
  };

  // Fetch and display problems
  const fetchProblems = async () => {
    try {
      const problems = await apiRequest(problemEndpoint);
      renderProblems(problems);
    } catch (error) {
      console.error('Error fetching problems:', error);
    }
  };

  const renderProblems = (problems) => {
    const problemList = document.getElementById('problem-list');
    problemList.innerHTML = '';
    problems.forEach((problem) => {
      const listItem = document.createElement('li');
      listItem.className = 'problem-item';
      listItem.innerHTML = `
        <h3>${problem.title}</h3>
        <p>${problem.description}</p>
        <button class="view-problem" data-id="${problem.id}">View</button>
      `;
      problemList.appendChild(listItem);
    });
  };

  // Handle problem view button click
  const handleProblemView = async (event) => {
    if (event.target.classList.contains('view-problem')) {
      const problemId = event.target.dataset.id;
      try {
        const problem = await apiRequest(`${problemEndpoint}/${problemId}`);
        displayProblemDetail(problem);
      } catch (error) {
        console.error('Error fetching problem details:', error);
      }
    }
  };

  const displayProblemDetail = (problem) => {
    const problemDetail = document.getElementById('problem-detail');
    problemDetail.innerHTML = `
      <h2>${problem.title}</h2>
      <p>${problem.description}</p>
      <textarea id="solution-input" placeholder="Write your solution here..."></textarea>
      <button id="submit-solution" data-id="${problem.id}">Submit Solution</button>
    `;
  };

  // Handle solution submission
  const handleSolutionSubmit = async (event) => {
    if (event.target.id === 'submit-solution') {
      const problemId = event.target.dataset.id;
      const solutionInput = document.getElementById('solution-input').value;
      try {
        const result = await apiRequest(solutionEndpoint, 'POST', {
          problem_id: problemId,
          solution: solutionInput,
        });
        alert(`Solution submitted: ${result.message}`);
      } catch (error) {
        console.error('Error submitting solution:', error);
      }
    }
  };

  // Attach event listeners
  document.getElementById('problem-list').addEventListener('click', handleProblemView);
  document.getElementById('problem-detail').addEventListener('click', handleSolutionSubmit);

  // Initial data load
  fetchProblems();
});