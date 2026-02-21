// Path: static/js/scripts.js
// Purpose: JavaScript file for adding interactivity to the app.

// Function to handle creating a new note
async function createNote() {
    const title = document.getElementById("note-title").value;
    const content = document.getElementById("note-content").value;

    const response = await fetch('/notes', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ title, content })
    });

    if (response.ok) {
        alert("Note created successfully!");
        location.reload();
    } else {
        alert("Failed to create note. Please try again.");
    }
}

// Function to handle deleting a note
async function deleteNote(noteId) {
    const response = await fetch(`/notes/${noteId}`, {
        method: 'DELETE'
    });

    if (response.ok) {
        alert("Note deleted successfully!");
        location.reload();
    } else {
        alert("Failed to delete note. Please try again.");
    }
}

// Function to handle updating a note
async function updateNote(noteId) {
    const title = document.getElementById(`note-title-${noteId}`).value;
    const content = document.getElementById(`note-content-${noteId}`).value;

    const response = await fetch(`/notes/${noteId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ title, content })
    });

    if (response.ok) {
        alert("Note updated successfully!");
        location.reload();
    } else {
        alert("Failed to update note. Please try again.");
    }
}

// Function to search for notes
async function searchNotes() {
    const query = document.getElementById("search-query").value;

    const response = await fetch(`/notes/search?q=${encodeURIComponent(query)}`, {
        method: 'GET'
    });

    if (response.ok) {
        const notes = await response.json();
        renderSearchResults(notes);
    } else {
        alert("Failed to search notes. Please try again.");
    }
}

// Function to render search results
function renderSearchResults(notes) {
    const resultsContainer = document.getElementById("search-results");
    resultsContainer.innerHTML = "";

    if (notes.length === 0) {
        resultsContainer.innerHTML = "<p>No notes found.</p>";
        return;
    }

    notes.forEach(note => {
        const noteElement = document.createElement("div");
        noteElement.className = "note";
        noteElement.innerHTML = `
            <h3>${note.title}</h3>
            <p>${note.content}</p>
        `;
        resultsContainer.appendChild(noteElement);
    });
}

// Attach event listeners to buttons
document.getElementById("create-note-btn")?.addEventListener("click", createNote);
document.getElementById("search-btn")?.addEventListener("click", searchNotes);
document.querySelectorAll(".delete-note-btn").forEach(button => {
    button.addEventListener("click", () => deleteNote(button.dataset.noteId));
});
document.querySelectorAll(".update-note-btn").forEach(button => {
    button.addEventListener("click", () => updateNote(button.dataset.noteId));
});