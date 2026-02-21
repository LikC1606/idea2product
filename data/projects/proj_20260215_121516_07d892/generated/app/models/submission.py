from datetime import datetime
from app.database import db

class Submission(db.Model):
    __tablename__ = 'submissions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Pending')  # e.g., Pending, Accepted, Rejected
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    execution_time = db.Column(db.Float, nullable=True)  # Time in seconds
    memory_used = db.Column(db.Integer, nullable=True)  # Memory in KB

    user = db.relationship('User', back_populates='submissions')
    problem = db.relationship('Problem', back_populates='submissions')

    def __repr__(self):
        return f"<Submission id={self.id} user_id={self.user_id} problem_id={self.problem_id} status={self.status}>"

# Back-population relationships in User and Problem models:
# In User model:
# submissions = db.relationship('Submission', back_populates='user', cascade='all, delete-orphan')
# In Problem model:
# submissions = db.relationship('Submission', back_populates='problem', cascade='all, delete-orphan')