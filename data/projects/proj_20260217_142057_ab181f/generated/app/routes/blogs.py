from flask import Blueprint, request, jsonify
from app import db
from app.models.blog import Blog
from app.utils.image_upload import upload_image
from flask import current_app

blogs_bp = Blueprint('blogs', __name__)

@blogs_bp.route('/blogs', methods=['GET'])
def get_blogs():
    blogs = Blog.query.all()
    return jsonify([blog.to_dict() for blog in blogs])

@blogs_bp.route('/blogs', methods=['POST'])
def create_blog():
    if 'image' not in request.files:
        return jsonify({'error': 'No image part'}), 400

    file = request.files['image']
    image_url = upload_image(file)

    if image_url is None:
        return jsonify({'error': 'Invalid image format'}), 400

    data = request.form
    blog = Blog(title=data['title'], content=data['content'], image_url=image_url)
    db.session.add(blog)
    db.session.commit()
    return jsonify(blog.to_dict()), 201
