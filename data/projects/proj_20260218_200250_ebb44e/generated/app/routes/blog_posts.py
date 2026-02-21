from flask import Blueprint, request, jsonify
from app import db
from app.models.blog_post import BlogPost
import os
from werkzeug.utils import secure_filename

blog_posts_bp = Blueprint('blog_posts', __name__)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@blog_posts_bp.route('/blog_posts', methods=['GET'])
def get_blog_posts():
    posts = BlogPost.query.all()
    return jsonify([post.to_dict() for post in posts])

@blog_posts_bp.route('/blog_posts', methods=['POST'])
def create_blog_post():
    title = request.form.get('title')
    content = request.form.get('content')
    image = request.files.get('image')

    if not title or not content:
        return jsonify({'error': 'Title and content are required'}), 400

    image_url = None
    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        image_path = os.path.join(UPLOAD_FOLDER, filename)
        image.save(image_path)
        image_url = '/' + image_path

    post = BlogPost(title=title, content=content, image_url=image_url)
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_dict()), 201

@blog_posts_bp.route('/blog_posts/<int:post_id>', methods=['PUT'])
def update_blog_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    data = request.get_json()

    post.title = data.get('title', post.title)
    post.content = data.get('content', post.content)
    db.session.commit()
    return jsonify(post.to_dict())

@blog_posts_bp.route('/blog_posts/<int:post_id>', methods=['DELETE'])
def delete_blog_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return jsonify({'message': 'Post deleted'})