// static/js/app.js

// Function to make an API request
async function fetchAPI(endpoint, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(endpoint, options);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    } catch (error) {
        console.error('Error fetching API:', error);
        throw error;
    }
}

// Function to handle note creation
async function createNote() {
    const title = document.getElementById('note-title').value;
    const content = document.getElementById('note-content').value;

    if (!title || !content) {
        alert('Title and content cannot be empty!');
        return;
    }

    try {
        const response = await fetchAPI('/api/notes', 'POST', {
            title: title,
            content: content,
        });
        alert('Note created successfully!');
        window.location.reload();
    } catch (error) {
        alert('Failed to create note. Please try again.');
    }
}

// Function to search notes
async function searchNotes() {
    const query = document.getElementById('search-query').value;

    try {
        const results = await fetchAPI(`/api/notes/search?q=${encodeURIComponent(query)}`);
        renderNotes(results);
    } catch (error) {
        alert('Failed to search notes. Please try again.');
    }
}

// Function to render notes on the page
function renderNotes(notes) {
    const notesContainer = document.getElementById('notes-container');
    notesContainer.innerHTML = '';

    if (notes.length === 0) {
        notesContainer.innerHTML = '<p>No notes found.</p>';
        return;
    }

    notes.forEach(note => {
        const noteElement = document.createElement('div');
        noteElement.className = 'note';
        noteElement.innerHTML = `
            <h3>${note.title}</h3>
            <p>${note.content}</p>
        `;
        notesContainer.appendChild(noteElement);
    });
}

// Event listeners
document.getElementById('create-note-btn').addEventListener('click', createNote);
document.getElementById('search-btn').addEventListener('click', searchNotes);