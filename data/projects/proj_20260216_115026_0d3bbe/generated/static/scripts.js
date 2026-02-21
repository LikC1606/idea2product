document.getElementById('saveButton').addEventListener('click', () => {
    const noteContent = document.getElementById('noteInput').value;
    if (noteContent.trim() === '') {
        alert('Please enter a note before saving.');
        return;
    }
    fetch('/save-note', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ note: noteContent }),
    })
    .then(response => {
        if (response.ok) {
            alert('Note saved successfully!');
            document.getElementById('noteInput').value = '';
        } else {
            alert('Failed to save the note. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while saving the note.');
    });
});