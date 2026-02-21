from flask import Blueprint, request, jsonify
from app.models.blog_post import BlogPost
from app import db
from app.utils.image_upload import upload_image

blog_posts_bp = Blueprint('blog_posts', __name__)

@blog_posts_bp.route('/blog_posts', methods=['GET'])
def get_blog_posts():
    posts = BlogPost.query.all()
    return jsonify([post.to_dict() for post in posts])

@blog_posts_bp.route('/blog_posts', methods=['POST'])
def create_blog_post():
    data = request.form
    image = request.files.get('image')
    image_url = None

    if image:
        try:
            image_url = upload_image(image)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    new_post = BlogPost(
        title=data['title'],
        description=data['description'],
        image_url=image_url
    )
    db.session.add(new_post)
    db.session.commit()
    return jsonify(new_post.to_dict()), 201

@blog_posts_bp.route('/blog_posts/<int:id>', methods=['PUT'])
def update_blog_post(id):
    data = request.get_json()
    post = BlogPost.query.get_or_404(id)
    post.title = data['title']
    post.description = data['description']
    post.image_url = data.get('image_url')
    db.session.commit()
    return jsonify(post.to_dict())

@blog_posts_bp.route('/blog_posts/<int:id>', methods=['DELETE'])
def delete_blog_post(id):
    post = BlogPost.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    return '', 204