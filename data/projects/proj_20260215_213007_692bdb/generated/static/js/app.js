// static/js/app.js

// Purpose: Handles frontend logic for the note-taking application.
// Layer: Frontend

document.addEventListener("DOMContentLoaded", () => {
    const noteForm = document.getElementById("noteForm");
    const noteInput = document.getElementById("noteInput");
    const noteList = document.getElementById("noteList");

    // Fetch existing notes from the database when the page loads
    fetch("/api/notes")
        .then(response => response.json())
        .then(data => {
            if (data.notes && Array.isArray(data.notes)) {
                data.notes.forEach(note => {
                    addNoteToList(note);
                });
            }
        })
        .catch(err => console.error("Error fetching notes:", err));

    // Add new note to the database and update the frontend
    noteForm.addEventListener("submit", event => {
        event.preventDefault();
        const noteContent = noteInput.value.trim();

        if (noteContent) {
            fetch("/api/notes", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ content: noteContent }),
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.note) {
                        addNoteToList(data.note);
                        noteInput.value = ""; // Clear the input field
                    } else {
                        console.error("Error saving note:", data.error);
                    }
                })
                .catch(err => console.error("Error saving note:", err));
        }
    });

    // Function to add a note to the list on the frontend
    function addNoteToList(note) {
        const listItem = document.createElement("li");
        listItem.textContent = note.content;
        noteList.appendChild(listItem);
    }
});