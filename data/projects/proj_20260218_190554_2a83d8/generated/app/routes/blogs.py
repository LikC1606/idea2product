from flask import Blueprint, request, jsonify
from app import db
from app.models.blog import Blog
from app.models.image import Image
import os
from werkzeug.utils import secure_filename

blogs_bp = Blueprint('blogs', __name__)
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@blogs_bp.route('/blogs', methods=['GET'])
def get_blogs():
    blogs = Blog.query.all()
    return jsonify([blog.to_dict() for blog in blogs])

@blogs_bp.route('/blogs', methods=['POST'])
def create_blog():
    data = request.form
    title = data.get('title')
    content = data.get('content')

    if not title or not content:
        return jsonify({'error': 'Title and content are required'}), 400

    blog = Blog(title=title, content=content)
    db.session.add(blog)
    db.session.commit()

    # Handle image upload
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)

            image = Image(blog_id=blog.id, image_url=file_path)
            db.session.add(image)
            db.session.commit()

    return jsonify(blog.to_dict()), 201

@blogs_bp.route('/blogs/<int:blog_id>', methods=['GET'])
def get_blog(blog_id):
    blog = Blog.query.get(blog_id)
    if not blog:
        return jsonify({'error': 'Blog not found'}), 404

    images = Image.query.filter_by(blog_id=blog_id).all()
    blog_data = blog.to_dict()
    blog_data['images'] = [image.to_dict() for image in images]

    return jsonify(blog_data)

@blogs_bp.route('/blogs/<int:blog_id>', methods=['PUT'])
def update_blog(blog_id):
    blog = Blog.query.get(blog_id)
    if not blog:
        return jsonify({'error': 'Blog not found'}), 404

    data = request.get_json()
    blog.title = data.get('title', blog.title)
    blog.content = data.get('content', blog.content)

    db.session.commit()
    return jsonify(blog.to_dict())

@blogs_bp.route('/blogs/<int:blog_id>', methods=['DELETE'])
def delete_blog(blog_id):
    blog = Blog.query.get(blog_id)
    if not blog:
        return jsonify({'error': 'Blog not found'}), 404

    db.session.delete(blog)
    db.session.commit()
    return '', 204

@blogs_bp.route('/images', methods=['POST'])
def upload_image():
    if 'blog_id' not in request.form or 'image' not in request.files:
        return jsonify({'error': 'Blog ID and image are required'}), 400

    blog_id = request.form['blog_id']
    file = request.files['image']

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    image = Image(blog_id=blog_id, image_url=file_path)
    db.session.add(image)
    db.session.commit()

    return jsonify(image.to_dict()), 201