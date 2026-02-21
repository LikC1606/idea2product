from app.database import db
from datetime import datetime

class Tutorial(db.Model):
    __tablename__ = 'tutorials'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    problem = db.relationship('Problem', back_populates='tutorials')
    hints = db.relationship('Hint', back_populates='tutorial', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Tutorial id={self.id} title={self.title}>"

class Hint(db.Model):
    __tablename__ = 'hints'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    tutorial_id = db.Column(db.Integer, db.ForeignKey('tutorials.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    tutorial = db.relationship('Tutorial', back_populates='hints')

    def __repr__(self):
        return f"<Hint id={self.id} tutorial_id={self.tutorial_id}>"