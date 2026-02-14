// app/static/js/scripts.js

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function () {
    // DOM Elements
    const uploadButton = document.getElementById('uploadButton');
    const inputDescription = document.getElementById('inputDescription');
    const generateButton = document.getElementById('generateButton');
    const resultTitle = document.getElementById('resultTitle');
    const resultSellingPoints = document.getElementById('resultSellingPoints');
    const imagePreview = document.getElementById('imagePreview');
    const errorMessage = document.getElementById('errorMessage');

    // Helper function to display error messages
    function displayError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        setTimeout(() => {
            errorMessage.style.display = 'none';
        }, 3000);
    }

    // Handle image upload and preview
    uploadButton.addEventListener('change', function (event) {
        const file = event.target.files[0];
        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function (e) {
                imagePreview.src = e.target.result;
                imagePreview.style.display = 'block';
            };
            reader.readAsDataURL(file);
        } else {
            displayError('Please upload a valid image file.');
        }
    });

    // Handle generate content button click
    generateButton.addEventListener('click', async function () {
        const description = inputDescription.value.trim();

        if (!uploadButton.files[0]) {
            displayError('Please upload a product image.');
            return;
        }

        if (!description) {
            displayError('Please enter a description.');
            return;
        }

        // Clear previous results
        resultTitle.textContent = '';
        resultSellingPoints.innerHTML = '';

        try {
            // Show loading state
            generateButton.textContent = 'Generating...';
            generateButton.disabled = true;

            // Simulate API request
            const formData = new FormData();
            formData.append('image', uploadButton.files[0]);
            formData.append('description', description);

            const response = await fetch('/api/generate', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Failed to generate product content. Please try again.');
            }

            const data = await response.json();

            // Display results
            resultTitle.textContent = data.title;
            data.sellingPoints.forEach((point) => {
                const li = document.createElement('li');
                li.textContent = point;
                resultSellingPoints.appendChild(li);
            });
        } catch (error) {
            displayError(error.message);
        } finally {
            // Reset button state
            generateButton.textContent = 'Generate';
            generateButton.disabled = false;
        }
    });
});