from app.database import db

class Solution(db.Model):
    __tablename__ = 'solutions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pending')
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    user = db.relationship('User', backref=db.backref('solutions', lazy=True))
    problem = db.relationship('Problem', backref=db.backref('solutions', lazy=True))

    def __init__(self, user_id, problem_id, code, language, status='Pending'):
        self.user_id = user_id
        self.problem_id = problem_id
        self.code = code
        self.language = language
        self.status = status

    def __repr__(self):
        return f"<Solution id={self.id} user_id={self.user_id} problem_id={self.problem_id} status={self.status}>"