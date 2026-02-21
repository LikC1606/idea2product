document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('note-form');
    const noteInput = document.getElementById('note-input');
    const notesList = document.getElementById('notes-list');

    // Fetch and display saved notes
    const fetchNotes = async () => {
        try {
            const response = await fetch('/api/notes');
            const notes = await response.json();
            notesList.innerHTML = '';
            notes.forEach(note => {
                const li = document.createElement('li');
                li.textContent = note.content;
                notesList.appendChild(li);
            });
        } catch (error) {
            console.error('Error fetching notes:', error);
        }
    };

    // Save a new note
    const saveNote = async (content) => {
        try {
            await fetch('/api/notes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content }),
            });
            fetchNotes();
        } catch (error) {
            console.error('Error saving note:', error);
        }
    };

    // Handle form submission
    form.addEventListener('submit', (event) => {
        event.preventDefault();
        const content = noteInput.value.trim();
        if (content) {
            saveNote(content);
            noteInput.value = '';
        }
    });

    // Initial fetch of notes
    fetchNotes();
});