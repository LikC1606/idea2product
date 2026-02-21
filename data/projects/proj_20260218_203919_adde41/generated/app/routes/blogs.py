from flask import Blueprint, request, jsonify
from app import db
from app.models.blog import Blog
from app.utils.image_upload import upload_image

blogs_bp = Blueprint('blogs', __name__)

@blogs_bp.route('/blogs', methods=['GET'])
def get_blogs():
    blogs = Blog.query.all()
    return jsonify([blog.to_dict() for blog in blogs])

@blogs_bp.route('/blogs', methods=['POST'])
def create_blog():
    data = request.form
    file = request.files.get('image')

    image_url = None
    if file:
        try:
            image_url = upload_image(file)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    blog = Blog(
        title=data.get('title'),
        content=data.get('content'),
        image_url=image_url
    )
    db.session.add(blog)
    db.session.commit()
    return jsonify(blog.to_dict()), 201

@blogs_bp.route('/blogs/<int:blog_id>', methods=['PUT'])
def update_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    data = request.form
    file = request.files.get('image')

    if 'title' in data:
        blog.title = data['title']
    if 'content' in data:
        blog.content = data['content']
    if file:
        try:
            blog.image_url = upload_image(file)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    db.session.commit()
    return jsonify(blog.to_dict())

@blogs_bp.route('/blogs/<int:blog_id>', methods=['DELETE'])
def delete_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    db.session.delete(blog)
    db.session.commit()
    return '', 204