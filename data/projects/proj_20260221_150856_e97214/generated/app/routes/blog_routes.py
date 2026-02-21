from flask import Blueprint, request, jsonify
from app.models.blog import Blog
from app import db
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'app/static/uploads'
blog_bp = Blueprint('blog', __name__)

# Helper function to save image
def save_image(image):
    filename = secure_filename(image.filename)
    image_path = os.path.join(UPLOAD_FOLDER, filename)
    image.save(image_path)
    return f'/static/uploads/{filename}'

@blog_bp.route('/', methods=['GET'])
def get_blogs():
    blogs = Blog.query.all()
    return jsonify([blog.to_dict() for blog in blogs])

@blog_bp.route('/', methods=['POST'])
def create_blog():
    data = request.form
    title = data.get('title')
    content = data.get('content')
    image = request.files.get('image')

    if not title or not content:
        return jsonify({'error': 'Title and content are required'}), 400

    image_path = save_image(image) if image else None

    blog = Blog(title=title, content=content, image_path=image_path)
    db.session.add(blog)
    db.session.commit()

    return jsonify(blog.to_dict()), 201

@blog_bp.route('/<int:id>', methods=['GET'])
def get_blog(id):
    blog = Blog.query.get_or_404(id)
    return jsonify(blog.to_dict())

@blog_bp.route('/<int:id>', methods=['PUT'])
def update_blog(id):
    blog = Blog.query.get_or_404(id)
    data = request.form
    title = data.get('title')
    content = data.get('content')
    image = request.files.get('image')

    if title:
        blog.title = title
    if content:
        blog.content = content
    if image:
        blog.image_path = save_image(image)

    db.session.commit()
    return jsonify(blog.to_dict())

@blog_bp.route('/<int:id>', methods=['DELETE'])
def delete_blog(id):
    blog = Blog.query.get_or_404(id)
    db.session.delete(blog)
    db.session.commit()
    return jsonify({'message': 'Blog deleted successfully'})