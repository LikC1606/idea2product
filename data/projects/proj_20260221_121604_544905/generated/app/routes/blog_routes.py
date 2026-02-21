from flask import Blueprint, request, jsonify
from app.models.blog import Blog
from app import db

blogs_bp = Blueprint('blogs', __name__)

@blogs_bp.route('/', methods=['GET'])
def get_blogs():
    blogs = Blog.query.all()
    return jsonify([blog.to_dict() for blog in blogs])

@blogs_bp.route('/', methods=['POST'])
def create_blog():
    data = request.get_json()
    new_blog = Blog(
        title=data['title'],
        description=data['description'],
        image_url=data.get('image_url')
    )
    db.session.add(new_blog)
    db.session.commit()
    return jsonify(new_blog.to_dict()), 201

@blogs_bp.route('/<int:blog_id>', methods=['GET'])
def get_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    return jsonify(blog.to_dict())

@blogs_bp.route('/<int:blog_id>', methods=['PUT'])
def update_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    data = request.get_json()
    blog.title = data['title']
    blog.description = data['description']
    blog.image_url = data.get('image_url')
    db.session.commit()
    return jsonify(blog.to_dict())

@blogs_bp.route('/<int:blog_id>', methods=['DELETE'])
def delete_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    db.session.delete(blog)
    db.session.commit()
    return jsonify({'message': 'Blog deleted successfully'})