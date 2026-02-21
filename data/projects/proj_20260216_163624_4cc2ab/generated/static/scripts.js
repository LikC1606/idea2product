document.addEventListener('DOMContentLoaded', () => {
    const noteForm = document.getElementById('note-form');
    const notesList = document.getElementById('notes-list');
    const searchInput = document.getElementById('search');
    const searchResults = document.getElementById('search-results');

    async function fetchNotes() {
        const response = await fetch('/api/notes');
        const notes = await response.json();
        renderNotes(notes);
    }

    async function createNote(event) {
        event.preventDefault();
        const title = document.getElementById('title').value;
        const content = document.getElementById('content').value;

        const response = await fetch('/api/notes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title, content })
        });

        if (response.ok) {
            fetchNotes();
            noteForm.reset();
        }
    }

    function renderNotes(notes) {
        notesList.innerHTML = '';
        notes.forEach(note => {
            const noteElement = document.createElement('div');
            noteElement.textContent = `${note.title}: ${note.content}`;
            notesList.appendChild(noteElement);
        });
    }

    async function searchNotes() {
        const query = searchInput.value;
        const response = await fetch('/api/notes');
        const notes = await response.json();
        const filteredNotes = notes.filter(note => 
            note.title.includes(query) || note.content.includes(query)
        );
        renderSearchResults(filteredNotes);
    }

    function renderSearchResults(notes) {
        searchResults.innerHTML = '';
        notes.forEach(note => {
            const noteElement = document.createElement('div');
            noteElement.textContent = `${note.title}: ${note.content}`;
            searchResults.appendChild(noteElement);
        });
    }

    noteForm.addEventListener('submit', createNote);
    searchInput.addEventListener('input', searchNotes);

    fetchNotes();
});