from app.database import db

class Solution(db.Model):
    __tablename__ = 'solutions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    submitted_code = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    submission_time = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    def __init__(self, user_id, problem_id, submitted_code, is_correct=False):
        self.user_id = user_id
        self.problem_id = problem_id
        self.submitted_code = submitted_code
        self.is_correct = is_correct

    def save(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_by_id(solution_id):
        return Solution.query.get(solution_id)

    @staticmethod
    def get_by_user(user_id):
        return Solution.query.filter_by(user_id=user_id).all()

    @staticmethod
    def get_by_problem(problem_id):
        return Solution.query.filter_by(problem_id=problem_id).all()