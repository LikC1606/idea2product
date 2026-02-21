document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('search-form');
    searchForm.addEventListener('submit', (event) => {
        const queryInput = searchForm.querySelector('input[name="query"]');
        if (!queryInput.value.trim()) {
            event.preventDefault();
            alert('Please enter a search query.');
        }
    });
});