document.addEventListener('DOMContentLoaded', () => {
    const noteForm = document.getElementById('note-form');
    const notesList = document.getElementById('notes-list');

    const fetchNotes = async () => {
        const response = await fetch('/api/notes');
        const notes = await response.json();
        notesList.innerHTML = '';
        notes.forEach(note => {
            const noteItem = document.createElement('li');
            noteItem.innerHTML = `
                <strong>${note.title}</strong>
                <p>${note.content}</p>
                <button onclick="deleteNote(${note.id})">Delete</button>
                <button onclick="editNote(${note.id})">Edit</button>
            `;
            notesList.appendChild(noteItem);
        });
    };

    const createNote = async (event) => {
        event.preventDefault();

        const title = document.getElementById('title').value;
        const content = document.getElementById('content').value;

        const response = await fetch('/api/notes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, content })
        });

        if (response.ok) {
            await fetchNotes();
            noteForm.reset();
        } else {
            alert('Failed to create note');
        }
    };

    const deleteNote = async (id) => {
        const response = await fetch(`/api/notes/${id}`, { method: 'DELETE' });
        if (response.ok) {
            await fetchNotes();
        } else {
            alert('Failed to delete note');
        }
    };

    const editNote = async (id) => {
        const title = prompt('Enter new title:');
        const content = prompt('Enter new content:');

        if (title && content) {
            const response = await fetch(`/api/notes/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, content })
            });

            if (response.ok) {
                await fetchNotes();
            } else {
                alert('Failed to update note');
            }
        }
    };

    noteForm.addEventListener('submit', createNote);
    fetchNotes();
});
