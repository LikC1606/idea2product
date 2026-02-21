// app/static/js/problem.js

// Purpose: Interface layer for managing problem interactions within the frontend.
// Functionality: Provides methods to fetch, create, update, and delete problems via API calls.
// Dependencies: Problem-related routes and controllers.

const ProblemAPI = {
  baseUrl: "/problems",

  /**
   * Fetch all problems
   * @returns {Promise} - Resolves to the list of problems
   */
  async fetchProblems() {
    try {
      const response = await fetch(this.baseUrl, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });
      return await response.json();
    } catch (error) {
      console.error("Error fetching problems:", error);
      throw error;
    }
  },

  /**
   * Fetch a single problem by ID
   * @param {number} problemId - ID of the problem to fetch
   * @returns {Promise} - Resolves to the problem details
   */
  async fetchProblem(problemId) {
    try {
      const response = await fetch(`${this.baseUrl}/${problemId}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });
      return await response.json();
    } catch (error) {
      console.error(`Error fetching problem with ID ${problemId}:`, error);
      throw error;
    }
  },

  /**
   * Create a new problem
   * @param {Object} problemData - Problem details (title, description)
   * @returns {Promise} - Resolves to the created problem
   */
  async createProblem(problemData) {
    try {
      const response = await fetch(this.baseUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(problemData),
      });
      return await response.json();
    } catch (error) {
      console.error("Error creating problem:", error);
      throw error;
    }
  },

  /**
   * Update an existing problem
   * @param {number} problemId - ID of the problem to update
   * @param {Object} problemData - Updated problem details
   * @returns {Promise} - Resolves to the updated problem
   */
  async updateProblem(problemId, problemData) {
    try {
      const response = await fetch(`${this.baseUrl}/${problemId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(problemData),
      });
      return await response.json();
    } catch (error) {
      console.error(`Error updating problem with ID ${problemId}:`, error);
      throw error;
    }
  },

  /**
   * Delete a problem
   * @param {number} problemId - ID of the problem to delete
   * @returns {Promise} - Resolves when the problem is deleted
   */
  async deleteProblem(problemId) {
    try {
      const response = await fetch(`${this.baseUrl}/${problemId}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
      });
      return response.ok;
    } catch (error) {
      console.error(`Error deleting problem with ID ${problemId}:`, error);
      throw error;
    }
  },
};

// Example usage:
// ProblemAPI.fetchProblems().then(problems => console.log(problems));