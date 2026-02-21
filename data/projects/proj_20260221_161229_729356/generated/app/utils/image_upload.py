import os
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest

UPLOAD_FOLDER = 'app/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(image):
    """Save uploaded image to the uploads folder and return its URL."""
    if not allowed_file(image.filename):
        raise BadRequest('Invalid file format. Only PNG, JPG, JPEG, and GIF are allowed.')

    image.seek(0, os.SEEK_END)
    file_size = image.tell()
    image.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise BadRequest('File size exceeds the maximum limit of 2MB.')

    filename = secure_filename(image.filename)
    image_path = os.path.join(UPLOAD_FOLDER, filename)
    image.save(image_path)
    return f'/static/uploads/{filename}'