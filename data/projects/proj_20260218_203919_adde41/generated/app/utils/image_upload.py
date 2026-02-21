import os
from werkzeug.utils import secure_filename
from flask import current_app

def upload_image(file):
    """Handle image upload and save to the configured upload folder."""
    if not validate_file_type(file):
        raise ValueError("Invalid file type")

    filename = secure_filename(file.filename)
    upload_folder = current_app.config['UPLOAD_FOLDER']

    # Ensure the upload folder exists
    os.makedirs(upload_folder, exist_ok=True)

    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)

    return f'/uploads/{filename}'

def validate_file_type(file):
    """Validate the file type of the uploaded image."""
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in file.filename and \
           file.filename.rsplit('.', 1)[1].lower() in allowed_extensions