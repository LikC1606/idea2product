from app.database import db

class Solution(db.Model):
    __tablename__ = 'solutions'

    id = db.Column(db.Integer, primary_key=True)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(50), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    submitted_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    # Relationships
    problem = db.relationship('Problem', backref=db.backref('solutions', lazy=True))
    user = db.relationship('User', backref=db.backref('solutions', lazy=True))

    def __repr__(self):
        return f"<Solution id={self.id} problem_id={self.problem_id} user_id={self.user_id} is_correct={self.is_correct}>"