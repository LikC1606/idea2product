from flask import render_template, request, redirect, url_for, flash
from app import app, db
from app.forms import BlogPostForm, ImageUploadForm
from app.models import BlogPost, Image
from werkzeug.utils import secure_filename
import os

@app.route('/')
def index():
    posts = BlogPost.query.all()
    return render_template('index.html', posts=posts)

@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    form = BlogPostForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        new_post = BlogPost(title=title, content=content)
        db.session.add(new_post)
        db.session.commit()
        flash('Blog post created successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('create_post.html', form=form)

@app.route('/upload_image', methods=['GET', 'POST'])
def upload_image():
    form = ImageUploadForm()
    if form.validate_on_submit():
        image_file = form.image.data
        if image_file:
            filename = secure_filename(image_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(filepath)
            new_image = Image(filename=filename, filepath=filepath)
            db.session.add(new_image)
            db.session.commit()
            flash('Image uploaded successfully!', 'success')
            return redirect(url_for('index'))
    return render_template('upload_image.html', form=form)