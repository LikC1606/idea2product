document.addEventListener('DOMContentLoaded', function() {
    const blogImage = document.querySelector('.blog-image');
    const overlay = document.createElement('div');
    overlay.className = 'overlay';
    document.body.appendChild(overlay);

    blogImage.addEventListener('click', function() {
        if (!blogImage.classList.contains('zoomed')) {
            blogImage.classList.add('zoomed');
            overlay.style.display = 'block';
        } else {
            blogImage.classList.remove('zoomed');
            overlay.style.display = 'none';
        }
    });

    overlay.addEventListener('click', function() {
        blogImage.classList.remove('zoomed');
        overlay.style.display = 'none';
    });
});