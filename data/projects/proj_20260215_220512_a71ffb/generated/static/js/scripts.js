// static/js/scripts.js

// Wait for the DOM to fully load
document.addEventListener('DOMContentLoaded', function () {
    // Add event listeners or interactive features here

    // Example: Confirm before deleting a note
    const deleteButtons = document.querySelectorAll('.delete-button');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function (event) {
            const confirmDelete = confirm('Are you sure you want to delete this note?');
            if (!confirmDelete) {
                event.preventDefault(); // Prevent deletion if user cancels
            }
        });
    });

    // Example: Toggle visibility for organized notes
    const organizeToggle = document.querySelector('#organize-toggle');
    if (organizeToggle) {
        organizeToggle.addEventListener('click', function () {
            const organizedNotes = document.querySelector('#organized-notes');
            if (organizedNotes) {
                organizedNotes.classList.toggle('hidden'); // Toggle 'hidden' class
            }
        });
    }
});