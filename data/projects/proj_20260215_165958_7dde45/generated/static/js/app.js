// static/js/app.js

// Frontend JavaScript for API calls

// Function to make a GET request to fetch data from the API
async function fetchData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

// Function to make a POST request to send data to the API
async function postData(url, payload) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error posting data:', error);
    }
}

// Example: Fetch problems from the API
async function getProblems() {
    const problemsUrl = '/api/problems';
    const problems = await fetchData(problemsUrl);
    console.log('Fetched Problems:', problems);
    return problems;
}

// Example: Submit a solution to the API
async function submitSolution(problemId, solutionCode) {
    const solutionsUrl = `/api/problems/${problemId}/submit`;
    const payload = {
        code: solutionCode,
    };
    const result = await postData(solutionsUrl, payload);
    console.log('Submission Result:', result);
    return result;
}

// Example: Fetch user profile data from the API
async function getUserProfile(userId) {
    const userProfileUrl = `/api/users/${userId}`;
    const userProfile = await fetchData(userProfileUrl);
    console.log('User Profile:', userProfile);
    return userProfile;
}

// Example: Fetch leaderboard data
async function getLeaderboard() {
    const leaderboardUrl = '/api/leaderboard';
    const leaderboard = await fetchData(leaderboardUrl);
    console.log('Leaderboard:', leaderboard);
    return leaderboard;
}

// Exporting functions for external usage
export {
    fetchData,
    postData,
    getProblems,
    submitSolution,
    getUserProfile,
    getLeaderboard,
};