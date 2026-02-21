// notes.js

document.addEventListener('DOMContentLoaded', function() {
    const notesContainer = document.getElementById('notes-container');
    const noteForm = document.getElementById('note-form');

    async function fetchNotes() {
        try {
            const response = await fetch('/api/notes');
            const notes = await response.json();
            notesContainer.innerHTML = '';
            notes.forEach(note => {
                const noteElement = document.createElement('div');
                noteElement.textContent = `${note.id}: ${note.content} (${note.created_at})`;
                notesContainer.appendChild(noteElement);
            });
        } catch (error) {
            console.error('Error fetching notes:', error);
        }
    }

    async function createNote(content) {
        try {
            const response = await fetch('/api/notes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ content })
            });
            if (response.ok) {
                await fetchNotes();
            } else {
                console.error('Error creating note:', await response.text());
            }
        } catch (error) {
            console.error('Error creating note:', error);
        }
    }

    noteForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const noteInput = document.getElementById('note-input');
        const noteContent = noteInput.value;
        if (noteContent) {
            createNote(noteContent);
            noteInput.value = '';
        }
    });

    fetchNotes();
});
