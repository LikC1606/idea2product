// static/js/scripts.js

// Function to fetch all notes and display them
async function fetchNotes() {
    try {
        const response = await fetch('/notes');
        const notes = await response.json();

        const notesContainer = document.getElementById('notes-container');
        notesContainer.innerHTML = '';

        notes.forEach(note => {
            const noteElement = document.createElement('div');
            noteElement.classList.add('note');
            noteElement.innerHTML = `
                <h3>${note.title}</h3>
                <p>${note.content}</p>
                <button class="delete-btn" data-note-id="${note.id}">Delete</button>
            `;
            notesContainer.appendChild(noteElement);
        });

        attachDeleteEvent();
    } catch (error) {
        console.error('Error fetching notes:', error);
    }
}

// Function to create a new note
async function createNote() {
    const title = document.getElementById('note-title').value;
    const content = document.getElementById('note-content').value;

    if (title.trim() === '' || content.trim() === '') {
        alert('Title and content cannot be empty.');
        return;
    }

    try {
        const response = await fetch('/notes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title, content })
        });

        if (response.ok) {
            document.getElementById('note-title').value = '';
            document.getElementById('note-content').value = '';
            fetchNotes();
        } else {
            console.error('Error creating note:', await response.text());
        }
    } catch (error) {
        console.error('Error creating note:', error);
    }
}

// Function to delete a note
async function deleteNote(noteId) {
    try {
        const response = await fetch(`/notes/${noteId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            fetchNotes();
        } else {
            console.error('Error deleting note:', await response.text());
        }
    } catch (error) {
        console.error('Error deleting note:', error);
    }
}

// Attach delete event to buttons
function attachDeleteEvent() {
    const deleteButtons = document.querySelectorAll('.delete-btn');
    deleteButtons.forEach(button => {
        button.addEventListener('click', () => {
            const noteId = button.getAttribute('data-note-id');
            deleteNote(noteId);
        });
    });
}

// Event listener for creating a new note
document.getElementById('create-note-btn').addEventListener('click', createNote);

// Initial fetch of notes
document.addEventListener('DOMContentLoaded', fetchNotes);