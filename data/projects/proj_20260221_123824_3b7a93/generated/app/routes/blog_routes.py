from flask import Blueprint, request, jsonify
from app.models.blog import Blog
from app import db

blog_bp = Blueprint('blogs', __name__)

@blog_bp.route('/', methods=['GET'])
def get_blogs():
    blogs = Blog.query.all()
    return jsonify([blog.to_dict() for blog in blogs])

@blog_bp.route('/', methods=['POST'])
def create_blog():
    data = request.json
    new_blog = Blog(
        title=data['title'],
        description=data['description'],
        image_url=data.get('image_url')
    )
    db.session.add(new_blog)
    db.session.commit()
    return jsonify(new_blog.to_dict()), 201

@blog_bp.route('/<int:blog_id>', methods=['GET'])
def get_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    return jsonify(blog.to_dict())

@blog_bp.route('/<int:blog_id>', methods=['PUT'])
def update_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    data = request.json
    blog.title = data['title']
    blog.description = data['description']
    blog.image_url = data.get('image_url')
    db.session.commit()
    return jsonify(blog.to_dict())

@blog_bp.route('/<int:blog_id>', methods=['DELETE'])
def delete_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    db.session.delete(blog)
    db.session.commit()
    return jsonify({'message': 'Blog deleted successfully'})