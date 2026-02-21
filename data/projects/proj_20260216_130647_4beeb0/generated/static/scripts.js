document.addEventListener('DOMContentLoaded', () => {
    const noteForm = document.getElementById('noteForm');
    const noteContent = document.getElementById('noteContent');
    const notesList = document.getElementById('notes');

    const fetchNotes = async () => {
        const response = await fetch('/notes');
        const notes = await response.json();
        notesList.innerHTML = '';
        notes.forEach(note => {
            const listItem = document.createElement('li');
            listItem.textContent = `${note.content} (Created: ${new Date(note.created_at).toLocaleString()})`;
            notesList.appendChild(listItem);
        });
    };

    noteForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const content = noteContent.value.trim();
        if (!content) return;

        await fetch('/notes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });

        noteContent.value = '';
        fetchNotes();
    });

    fetchNotes();
});