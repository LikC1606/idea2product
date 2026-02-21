from flask import Blueprint, request, jsonify
from app.models.blog import Blog
from app import db
from app.utils.image_utils import save_image

blog_bp = Blueprint('blog', __name__)

@blog_bp.route('/', methods=['GET'])
def get_all_blogs():
    blogs = Blog.query.all()
    return jsonify([blog.to_dict() for blog in blogs])

@blog_bp.route('/<int:blog_id>', methods=['GET'])
def get_blog_by_id(blog_id):
    blog = Blog.query.get(blog_id)
    if not blog:
        return jsonify({'error': 'Blog not found'}), 404
    return jsonify(blog.to_dict())

@blog_bp.route('/', methods=['POST'])
def create_blog():
    data = request.form
    title = data.get('title')
    content = data.get('content')
    images = request.files.getlist('images')

    if not title or not content:
        return jsonify({'error': 'Title and content are required'}), 400

    image_urls = []
    for image in images:
        image_url = save_image(image)
        image_urls.append(image_url)

    blog = Blog(title=title, content=content, images=image_urls)
    db.session.add(blog)
    db.session.commit()

    return jsonify(blog.to_dict()), 201

@blog_bp.route('/<int:blog_id>', methods=['PUT'])
def update_blog(blog_id):
    blog = Blog.query.get(blog_id)
    if not blog:
        return jsonify({'error': 'Blog not found'}), 404

    data = request.form
    title = data.get('title')
    content = data.get('content')
    images = request.files.getlist('images')

    if title:
        blog.title = title
    if content:
        blog.content = content
    if images:
        image_urls = []
        for image in images:
            image_url = save_image(image)
            image_urls.append(image_url)
        blog.images = image_urls

    db.session.commit()

    return jsonify(blog.to_dict())

@blog_bp.route('/<int:blog_id>', methods=['DELETE'])
def delete_blog(blog_id):
    blog = Blog.query.get(blog_id)
    if not blog:
        return jsonify({'error': 'Blog not found'}), 404

    db.session.delete(blog)
    db.session.commit()

    return jsonify({'message': 'Blog deleted successfully'})