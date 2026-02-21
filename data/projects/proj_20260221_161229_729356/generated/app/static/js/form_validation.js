document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("blogForm");

    form.addEventListener("submit", function(event) {
        let isValid = true;

        // Title validation
        const title = document.getElementById("title");
        const titleError = document.getElementById("titleError");
        if (title.value.trim() === "") {
            titleError.textContent = "Title is required.";
            isValid = false;
        } else {
            titleError.textContent = "";
        }

        // Description validation
        const description = document.getElementById("description");
        const descriptionError = document.getElementById("descriptionError");
        if (description.value.trim() === "") {
            descriptionError.textContent = "Description is required.";
            isValid = false;
        } else {
            descriptionError.textContent = "";
        }

        // Image validation
        const image = document.getElementById("image");
        const imageError = document.getElementById("imageError");
        if (image.files.length > 0) {
            const file = image.files[0];
            const validImageTypes = ["image/jpeg", "image/png", "image/gif"];
            if (!validImageTypes.includes(file.type)) {
                imageError.textContent = "Only JPEG, PNG, and GIF files are allowed.";
                isValid = false;
            } else {
                imageError.textContent = "";
            }
        } else {
            imageError.textContent = "";
        }

        if (!isValid) {
            event.preventDefault();
        }
    });
});