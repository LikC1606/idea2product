import os
from werkzeug.utils import secure_filename

def save_image(image, upload_folder):
    """
    Save an uploaded image to the specified upload folder.

    Args:
        image (FileStorage): The uploaded image file.
        upload_folder (str): The folder where the image will be saved.

    Returns:
        str: The relative URL path to the saved image.
    """
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    filename = secure_filename(image.filename)
    file_path = os.path.join(upload_folder, filename)
    image.save(file_path)

    # Return the relative URL path to the image
    return f'/static/uploads/{filename}'