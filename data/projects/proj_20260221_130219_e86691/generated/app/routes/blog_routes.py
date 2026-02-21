from flask import Blueprint, request, jsonify
from app.models.blog import Blog
from app import db
from app.utils.image_handler import save_image
import os

blog_bp = Blueprint('blog', __name__)

UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads')

@blog_bp.route('/blogs', methods=['GET'])
def get_blogs():
    blogs = Blog.query.all()
    return jsonify([blog.to_dict() for blog in blogs])

@blog_bp.route('/blogs', methods=['POST'])
def create_blog():
    title = request.form.get('title')
    description = request.form.get('description')
    image = request.files.get('image')

    if not title or not description:
        return jsonify({'error': 'Title and description are required'}), 400

    image_url = None
    if image:
        image_url = save_image(image, UPLOAD_FOLDER)

    blog = Blog(title=title, description=description, image_url=image_url)
    db.session.add(blog)
    db.session.commit()

    return jsonify(blog.to_dict()), 201

@blog_bp.route('/blogs/<int:blog_id>', methods=['GET'])
def get_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    return jsonify(blog.to_dict())

@blog_bp.route('/blogs/<int:blog_id>', methods=['PUT'])
def update_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)

    title = request.form.get('title')
    description = request.form.get('description')
    image = request.files.get('image')

    if title:
        blog.title = title
    if description:
        blog.description = description
    if image:
        blog.image_url = save_image(image, UPLOAD_FOLDER)

    db.session.commit()
    return jsonify(blog.to_dict())

@blog_bp.route('/blogs/<int:blog_id>', methods=['DELETE'])
def delete_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    db.session.delete(blog)
    db.session.commit()
    return jsonify({'message': 'Blog deleted successfully'})