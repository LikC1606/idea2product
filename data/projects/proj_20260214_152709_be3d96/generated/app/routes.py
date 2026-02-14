from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
from app.controllers import generate_product_content
from app.models import validate_image

routes = Blueprint('routes', __name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@routes.route('/upload', methods=['POST'])
def upload_file():
    if 'image' not in request.files:
        return jsonify({'error': 'No image part in the request'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # Validate the uploaded image
        if not validate_image(file_path):
            os.remove(file_path)
            return jsonify({'error': 'Invalid image file'}), 400

        if 'description' not in request.form or not request.form['description']:
            return jsonify({'error': 'No description provided'}), 400

        description = request.form['description']

        # Generate product content using the controller
        product_content = generate_product_content(image_path=file_path, description=description)

        # Clean up the uploaded image after processing
        os.remove(file_path)

        return jsonify(product_content), 200
    else:
        return jsonify({'error': 'File not allowed'}), 400

@routes.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'Welcome to the Product Content Generator API!'}), 200