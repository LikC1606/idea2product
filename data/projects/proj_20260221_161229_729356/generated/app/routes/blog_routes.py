from flask import Blueprint, request, jsonify
from app.models.blog import Blog
from app import db
from app.utils.image_upload import save_image

blog_routes = Blueprint('blog_routes', __name__)

@blog_routes.route('/blogs', methods=['GET'])
def get_blogs():
    blogs = Blog.query.all()
    return jsonify([blog.to_dict() for blog in blogs])

@blog_routes.route('/blogs/<int:id>', methods=['GET'])
def get_blog(id):
    blog = Blog.query.get(id)
    if not blog:
        return jsonify({'error': 'Blog not found'}), 404
    return jsonify(blog.to_dict())

@blog_routes.route('/blogs', methods=['POST'])
def create_blog():
    data = request.form
    title = data.get('title')
    description = data.get('description')
    image = request.files.get('image')

    if not title or not description:
        return jsonify({'error': 'Title and description are required'}), 400

    image_url = save_image(image) if image else None

    blog = Blog(title=title, description=description, image_url=image_url)
    db.session.add(blog)
    db.session.commit()

    return jsonify(blog.to_dict()), 201

@blog_routes.route('/blogs/<int:id>', methods=['PUT'])
def update_blog(id):
    blog = Blog.query.get(id)
    if not blog:
        return jsonify({'error': 'Blog not found'}), 404

    data = request.form
    blog.title = data.get('title', blog.title)
    blog.description = data.get('description', blog.description)
    image = request.files.get('image')

    if image:
        blog.image_url = save_image(image)

    db.session.commit()
    return jsonify(blog.to_dict())

@blog_routes.route('/blogs/<int:id>', methods=['DELETE'])
def delete_blog(id):
    blog = Blog.query.get(id)
    if not blog:
        return jsonify({'error': 'Blog not found'}), 404

    db.session.delete(blog)
    db.session.commit()
    return jsonify({'message': 'Blog deleted successfully'})