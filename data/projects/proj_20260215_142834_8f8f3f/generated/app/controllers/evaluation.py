from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from app.models.problem import Problem
from app.models.submission import Submission
from app.database import get_db_session

evaluation_bp = Blueprint('evaluation', __name__)

@evaluation_bp.route('/submit', methods=['POST'])
def submit_code():
    db_session = get_db_session()
    data = request.json
    problem_id = data.get('problem_id')
    user_id = data.get('user_id')
    code = data.get('code')

    if not problem_id or not user_id or not code:
        return jsonify({'error': 'Missing required fields'}), 400

    problem = db_session.query(Problem).filter_by(id=problem_id).first()
    if not problem:
        return jsonify({'error': 'Problem not found'}), 404

    # Here you would normally include the code execution and evaluation logic
    # For the sake of example, we'll assume the code execution is successful
    is_correct = True  # Placeholder for actual evaluation result

    submission = Submission(problem_id=problem_id, user_id=user_id, code=code, is_correct=is_correct)
    db_session.add(submission)
    db_session.commit()

    return jsonify({'message': 'Submission successful', 'is_correct': is_correct}), 200

@evaluation_bp.route('/result/<int:submission_id>', methods=['GET'])
def get_submission_result(submission_id):
    db_session = get_db_session()
    submission = db_session.query(Submission).filter_by(id=submission_id).first()

    if not submission:
        return jsonify({'error': 'Submission not found'}), 404

    return jsonify({
        'submission_id': submission.id,
        'problem_id': submission.problem_id,
        'user_id': submission.user_id,
        'is_correct': submission.is_correct
    }), 200