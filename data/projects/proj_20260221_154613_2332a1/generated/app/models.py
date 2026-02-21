from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class BlogPost(db.Model):
    __tablename__ = 'blog_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)

    def __repr__(self):
        return f'<BlogPost {self.title}>'

class Image(db.Model):
    __tablename__ = 'images'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_url = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    blog_post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'), nullable=True)

    blog_post = db.relationship('BlogPost', backref=db.backref('images', lazy=True))

    def __repr__(self):
        return f'<Image {self.filename}>'