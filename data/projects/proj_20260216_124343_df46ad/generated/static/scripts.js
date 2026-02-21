document.addEventListener('DOMContentLoaded', () => {
    const noteForm = document.getElementById('noteForm');
    const noteContent = document.getElementById('noteContent');
    const notesList = document.getElementById('notesList');

    // Fetch and display saved notes
    async function fetchNotes() {
        try {
            const response = await fetch('/notes');
            const notes = await response.json();
            notesList.innerHTML = '';
            notes.forEach(note => {
                const listItem = document.createElement('li');
                listItem.innerHTML = `
                    <p>${note.content}</p>
                    <span class="date">Created At: ${new Date(note.created_at).toLocaleString()}</span>
                `;
                notesList.appendChild(listItem);
            });
        } catch (error) {
            console.error('Error fetching notes:', error);
        }
    }

    // Handle form submission
    noteForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const content = noteContent.value.trim();
        if (content) {
            try {
                const response = await fetch('/notes', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ content }),
                });

                if (response.ok) {
                    noteContent.value = '';
                    fetchNotes();
                } else {
                    console.error('Error saving note:', response.statusText);
                }
            } catch (error) {
                console.error('Error saving note:', error);
            }
        }
    });

    // Initially load notes
    fetchNotes();
});