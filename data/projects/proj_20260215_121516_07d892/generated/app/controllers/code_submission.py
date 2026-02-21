from flask import Blueprint, request, jsonify
from app.models.submission import Submission
from app.code_evaluation.environment import CodeEvaluationEnvironment

code_submission_bp = Blueprint('code_submission', __name__)

@code_submission_bp.route('/submit', methods=['POST'])
def submit_code():
    try:
        # Parse request data
        data = request.get_json()
        problem_id = data.get('problem_id')
        user_id = data.get('user_id')
        code = data.get('code')
        language = data.get('language')

        if not problem_id or not user_id or not code or not language:
            return jsonify({'error': 'Missing required fields'}), 400

        # Save the submission to the database
        submission = Submission(
            problem_id=problem_id,
            user_id=user_id,
            code=code,
            language=language,
            status='pending'
        )
        submission.save()

        # Evaluate the code in a secure environment
        evaluator = CodeEvaluationEnvironment()
        evaluation_result = evaluator.evaluate(submission)

        # Update submission status and result
        submission.status = evaluation_result['status']
        submission.output = evaluation_result.get('output', '')
        submission.error = evaluation_result.get('error', '')
        submission.save()

        # Return the evaluation result
        return jsonify({
            'submission_id': submission.id,
            'status': submission.status,
            'output': submission.output,
            'error': submission.error
        }), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500