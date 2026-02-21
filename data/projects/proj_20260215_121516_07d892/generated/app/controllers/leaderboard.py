from flask import Blueprint, jsonify
from app.models.leaderboard import Leaderboard
from app.database import db_session

leaderboard_bp = Blueprint('leaderboard', __name__)

@leaderboard_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """
    Endpoint to retrieve leaderboard data.
    Returns:
        JSON response containing user rankings based on scores.
    """
    try:
        # Fetch leaderboard data from the model
        leaderboard_data = Leaderboard.get_all_users_ranked()
        return jsonify({
            'status': 'success',
            'data': leaderboard_data
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@leaderboard_bp.route('/leaderboard/<int:user_id>', methods=['GET'])
def get_user_rank(user_id):
    """
    Endpoint to retrieve a specific user's rank.
    Args:
        user_id: ID of the user to fetch rank for.
    Returns:
        JSON response containing the user's rank and score.
    """
    try:
        user_rank = Leaderboard.get_user_rank(user_id)
        if user_rank:
            return jsonify({
                'status': 'success',
                'data': user_rank
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'User not found in leaderboard.'
            }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@leaderboard_bp.route('/leaderboard/reset', methods=['POST'])
def reset_leaderboard():
    """
    Endpoint to reset the leaderboard.
    Clears all scores and rankings.
    Returns:
        JSON response confirming the reset operation.
    """
    try:
        Leaderboard.reset_leaderboard()
        db_session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Leaderboard has been reset successfully.'
        }), 200
    except Exception as e:
        db_session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500