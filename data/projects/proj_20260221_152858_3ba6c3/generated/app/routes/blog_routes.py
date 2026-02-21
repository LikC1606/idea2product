import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from app.models.blog import Blog
from app import db

UPLOAD_FOLDER = 'app/static/uploads'

blog_bp = Blueprint('blog', __name__)

@blog_bp.route('/', methods=['GET'])
def get_blogs():
    blogs = Blog.query.all()
    return jsonify([blog.to_dict() for blog in blogs])

@blog_bp.route('/<int:id>', methods=['GET'])
def get_blog(id):
    blog = Blog.query.get_or_404(id)
    return jsonify(blog.to_dict())

@blog_bp.route('/', methods=['POST'])
def create_blog():
    title = request.form.get('title')
    description = request.form.get('description')
    image = request.files.get('image')

    if not title or not description:
        return jsonify({'error': 'Title and description are required'}), 400

    image_path = None
    if image:
        filename = secure_filename(image.filename)
        image.save(os.path.join(UPLOAD_FOLDER, filename))
        image_path = f'/static/uploads/{filename}'

    blog = Blog(title=title, description=description, image_path=image_path)
    db.session.add(blog)
    db.session.commit()

    return jsonify(blog.to_dict()), 201

@blog_bp.route('/<int:id>', methods=['PUT'])
def update_blog(id):
    blog = Blog.query.get_or_404(id)

    title = request.form.get('title')
    description = request.form.get('description')
    image = request.files.get('image')

    if title:
        blog.title = title
    if description:
        blog.description = description
    if image:
        filename = secure_filename(image.filename)
        image.save(os.path.join(UPLOAD_FOLDER, filename))
        blog.image_path = f'/static/uploads/{filename}'

    db.session.commit()

    return jsonify(blog.to_dict())

@blog_bp.route('/<int:id>', methods=['DELETE'])
def delete_blog(id):
    blog = Blog.query.get_or_404(id)
    db.session.delete(blog)
    db.session.commit()

    return jsonify({'message': 'Blog deleted successfully'})