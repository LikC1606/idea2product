from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from app.models.solution import Solution
from app.database import get_db_session

solution_controller = Blueprint('solution_controller', __name__)

@solution_controller.route('/submit_solution', methods=['POST'])
def submit_solution():
    data = request.json
    user_id = data.get('user_id')
    problem_id = data.get('problem_id')
    code = data.get('code')
    language = data.get('language')

    if not all([user_id, problem_id, code, language]):
        return jsonify({'error': 'Missing required fields'}), 400

    session: Session = get_db_session()
    
    try:
        solution = Solution(user_id=user_id, problem_id=problem_id, code=code, language=language)
        session.add(solution)
        session.commit()
        return jsonify({'message': 'Solution submitted successfully'}), 201
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@solution_controller.route('/solutions/<int:user_id>', methods=['GET'])
def get_user_solutions(user_id):
    session: Session = get_db_session()
    
    try:
        solutions = session.query(Solution).filter(Solution.user_id == user_id).all()
        solutions_data = [{'id': s.id, 'problem_id': s.problem_id, 'code': s.code, 'language': s.language} for s in solutions]
        return jsonify(solutions_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()