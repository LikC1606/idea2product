document.getElementById('blogForm').addEventListener('submit', function(event) {
    const imageInput = document.getElementById('image');
    const imageError = document.getElementById('imageError');
    const allowedExtensions = ['png', 'jpg', 'jpeg', 'gif'];
    const maxFileSize = 2 * 1024 * 1024; // 2MB

    imageError.textContent = '';

    if (imageInput.files.length > 0) {
        const file = imageInput.files[0];
        const fileExtension = file.name.split('.').pop().toLowerCase();

        if (!allowedExtensions.includes(fileExtension)) {
            imageError.textContent = 'Invalid file format. Only PNG, JPG, JPEG, and GIF are allowed.';
            event.preventDefault();
            return;
        }

        if (file.size > maxFileSize) {
            imageError.textContent = 'File size exceeds the maximum limit of 2MB.';
            event.preventDefault();
            return;
        }
    }
});