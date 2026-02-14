import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
from src.database.database_setup import Database

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Database setup
db = Database()

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload-image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Process image (e.g., resize or validate)
        try:
            with Image.open(filepath) as img:
                img.verify()
        except Exception as e:
            os.remove(filepath)
            return jsonify({'error': 'Invalid image file'}), 400

        # Save file info to the database
        try:
            db.insert_image(filename, filepath)
        except Exception as e:
            os.remove(filepath)
            return jsonify({'error': 'Database error', 'details': str(e)}), 500

        return jsonify({'message': 'Image uploaded successfully', 'filename': filename}), 200

    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/get-images', methods=['GET'])
def get_images():
    try:
        images = db.get_all_images()
        return jsonify({'images': images}), 200
    except Exception as e:
        return jsonify({'error': 'Database error', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)