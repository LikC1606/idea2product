from app.database import db
from app.models.problem import Problem
from app.models.user import User

class Solution(db.Model):
    __tablename__ = 'solutions'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(50), nullable=False)
    submission_time = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    problem = db.relationship('Problem', backref=db.backref('solutions', lazy=True))
    user = db.relationship('User', backref=db.backref('solutions', lazy=True))

    def __repr__(self):
        return f"<Solution id={self.id} user_id={self.user_id} problem_id={self.problem_id}>"

    def save(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_by_id(solution_id):
        return Solution.query.get(solution_id)

    @staticmethod
    def get_by_problem_and_user(problem_id, user_id):
        return Solution.query.filter_by(problem_id=problem_id, user_id=user_id).first()

    @staticmethod
    def get_all_by_user(user_id):
        return Solution.query.filter_by(user_id=user_id).all()

    @staticmethod
    def get_all_by_problem(problem_id):
        return Solution.query.filter_by(problem_id=problem_id).all()