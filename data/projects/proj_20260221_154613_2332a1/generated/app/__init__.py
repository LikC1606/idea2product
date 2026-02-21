from flask import Flask
from app.routes import index, create_post, upload_image
from app.forms import BlogPostForm, ImageUploadForm
from app.models import BlogPost, Image

def create_app():
    app = Flask(__name__)
    
    # Add configurations here if needed, e.g., app.config['UPLOAD_FOLDER'] = '/path/to/upload/folder'

    # Register routes
    app.add_url_rule('/', 'index', index)
    app.add_url_rule('/create-post', 'create_post', create_post, methods=['GET', 'POST'])
    app.add_url_rule('/upload-image', 'upload_image', upload_image, methods=['GET', 'POST'])

    return app