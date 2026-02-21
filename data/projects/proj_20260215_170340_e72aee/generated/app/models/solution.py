from app.database import db

class Solution(db.Model):
    __tablename__ = 'solutions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    submission_code = db.Column(db.Text, nullable=False)
    submission_date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    status = db.Column(db.String(50), nullable=False)
    execution_time = db.Column(db.Float, nullable=True)
    memory_used = db.Column(db.Float, nullable=True)

    # Relationships
    user = db.relationship('User', backref=db.backref('solutions', lazy=True))
    problem = db.relationship('Problem', backref=db.backref('solutions', lazy=True))