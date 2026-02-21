import os

from werkzeug.utils import secure_filename
def save_image(image, upload_folder):
    """
    Save an uploaded image to the specified folder.

    Args:
        image (FileStorage): The uploaded image file.
        upload_folder (str): The folder where the image will be saved.

    Returns:
        str: The URL path to the saved image (with leading slash for web access).
    """
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    filename = secure_filename(image.filename)
    image_path = os.path.join(upload_folder, filename)
    image.save(image_path)

    # Return URL path with leading slash for web access
    return image_path