// static/js/app.js

document.addEventListener('DOMContentLoaded', () => {
    // Event listener for creating a new note
    const createNoteButton = document.getElementById('create-note');
    if (createNoteButton) {
        createNoteButton.addEventListener('click', () => {
            const noteTitle = prompt('Enter the title of the note:');
            if (noteTitle) {
                // Send the new note to the backend
                fetch('/api/notes', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ title: noteTitle }),
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Note created successfully!');
                        location.reload(); // Reload the page to show the new note
                    } else {
                        alert('Error creating note: ' + data.message);
                    }
                })
                .catch(error => console.error('Error:', error));
            }
        });
    }

    // Event listener for searching notes
    const searchInput = document.getElementById('search-notes');
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            const query = searchInput.value.toLowerCase();
            const noteElements = document.querySelectorAll('.note');
            
            noteElements.forEach(note => {
                const title = note.querySelector('.note-title').textContent.toLowerCase();
                if (title.includes(query)) {
                    note.style.display = '';
                } else {
                    note.style.display = 'none';
                }
            });
        });
    }
});