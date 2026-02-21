import os
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'static/uploads'

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_image(file: FileStorage) -> bool:
    """Validate if the uploaded file is an image and has an allowed extension."""
    return file and allowed_file(file.filename)

def save_image(file: FileStorage) -> str:
    """Save the uploaded image to the upload folder and return its path."""
    if not validate_image(file):
        raise ValueError("Invalid image file")

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    return file_path