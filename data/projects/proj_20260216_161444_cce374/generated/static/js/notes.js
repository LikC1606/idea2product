document.addEventListener('DOMContentLoaded', function() {
    const notesList = document.getElementById('notes-list');
    const noteForm = document.getElementById('note-form');
    const noteInput = document.getElementById('note-input');

    // Fetch and display notes
    async function fetchNotes() {
        const response = await fetch('/api/notes');
        const notes = await response.json();
        notesList.innerHTML = '';
        notes.forEach(note => {
            const li = document.createElement('li');
            li.textContent = `${note.content} (Created at: ${note.created_at})`;
            notesList.appendChild(li);
        });
    }

    // Handle form submission
    noteForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        const content = noteInput.value;

        if (content) {
            const response = await fetch('/api/notes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ content })
            });

            if (response.ok) {
                noteInput.value = '';
                fetchNotes();
            } else {
                alert('Failed to create note');
            }
        } else {
            alert('Note content cannot be empty');
        }
    });

    // Initial fetch
    fetchNotes();
});