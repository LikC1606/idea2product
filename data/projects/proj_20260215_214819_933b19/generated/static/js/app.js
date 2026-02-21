document.addEventListener("DOMContentLoaded", function () {
    // Functions to handle notes operations
    const createNoteButton = document.getElementById("create-note-btn");
    const searchInput = document.getElementById("search-input");
    const notesContainer = document.getElementById("notes-container");

    // Fetch notes from the server and display them
    async function fetchNotes() {
        try {
            const response = await fetch("/api/notes");
            const notes = await response.json();
            renderNotes(notes);
        } catch (error) {
            console.error("Error fetching notes:", error);
        }
    }

    // Render notes in the container
    function renderNotes(notes) {
        notesContainer.innerHTML = ""; // Clear existing notes
        if (notes.length === 0) {
            notesContainer.innerHTML = "<p>No notes found</p>";
            return;
        }
        notes.forEach((note) => {
            const noteElement = document.createElement("div");
            noteElement.className = "note";
            noteElement.innerHTML = `
                <h3>${note.title}</h3>
                <p>${note.content}</p>
                <button class="delete-note-btn" data-id="${note.id}">Delete</button>
            `;
            notesContainer.appendChild(noteElement);
        });
    }

    // Create a new note
    async function createNote() {
        const title = prompt("Enter note title:");
        const content = prompt("Enter note content:");
        if (!title || !content) {
            alert("Both title and content are required!");
            return;
        }
        try {
            const response = await fetch("/api/notes", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ title, content }),
            });
            if (response.ok) {
                fetchNotes();
            } else {
                console.error("Error creating note:", await response.text());
            }
        } catch (error) {
            console.error("Error creating note:", error);
        }
    }

    // Delete a note
    async function deleteNote(noteId) {
        try {
            const response = await fetch(`/api/notes/${noteId}`, {
                method: "DELETE",
            });
            if (response.ok) {
                fetchNotes();
            } else {
                console.error("Error deleting note:", await response.text());
            }
        } catch (error) {
            console.error("Error deleting note:", error);
        }
    }

    // Search notes
    function searchNotes(query) {
        const allNotes = Array.from(notesContainer.querySelectorAll(".note"));
        allNotes.forEach((note) => {
            const title = note.querySelector("h3").textContent.toLowerCase();
            const content = note.querySelector("p").textContent.toLowerCase();
            if (title.includes(query) || content.includes(query)) {
                note.style.display = "block";
            } else {
                note.style.display = "none";
            }
        });
    }

    // Event listeners
    createNoteButton.addEventListener("click", createNote);
    searchInput.addEventListener("input", (e) => {
        const query = e.target.value.toLowerCase();
        searchNotes(query);
    });
    notesContainer.addEventListener("click", (e) => {
        if (e.target.classList.contains("delete-note-btn")) {
            const noteId = e.target.getAttribute("data-id");
            deleteNote(noteId);
        }
    });

    // Initial fetch of notes
    fetchNotes();
});