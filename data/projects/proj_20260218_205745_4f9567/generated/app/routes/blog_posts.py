from flask import Blueprint, request, jsonify
from app import db
from app.models.blog_post import BlogPost
from app.utils.image_upload import save_image

blog_posts_bp = Blueprint('blog_posts', __name__)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@blog_posts_bp.route('/blog_posts', methods=['GET'])
def get_blog_posts():
    posts = BlogPost.query.all()
    return jsonify([post.to_dict() for post in posts])

from werkzeug.utils import secure_filename
@blog_posts_bp.route('/blog_posts', methods=['POST'])
def create_blog_post():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    image = request.files['image']

    if image.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        image_path = save_image(image, UPLOAD_FOLDER)

        data = request.form
        title = data.get('title')
        description = data.get('description')

        if not title or not description:
            return jsonify({'error': 'Title and description are required'}), 400

        post = BlogPost(
            title=title,
            description=description,
            image_url=image_path
        )
        db.session.add(post)
        db.session.commit()

        return jsonify(post.to_dict()), 201

    return jsonify({'error': 'Invalid file type'}), 400