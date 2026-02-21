import os
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'static/uploads'

def validate_image(file: FileStorage) -> bool:
    """Validate if the uploaded file is an allowed image type."""
    return '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file: FileStorage, blog_id: int) -> str:
    """Save the image to the upload folder and return the file path."""
    if not validate_image(file):
        raise ValueError("Invalid file type")

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    # Ensure the upload folder exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    file.save(file_path)
    return file_path