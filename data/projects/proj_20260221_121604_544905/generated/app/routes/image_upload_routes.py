from flask import Blueprint, request, jsonify
import os
from werkzeug.utils import secure_filename

image_upload_bp = Blueprint('image_upload', __name__)

UPLOAD_FOLDER = 'app/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@image_upload_bp.route('/api/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        file_url = f'/static/uploads/{filename}'
        return jsonify({'message': 'File successfully uploaded', 'url': file_url}), 201
    else:
        return jsonify({'error': 'Allowed file types are png, jpg, jpeg, gif'}), 400