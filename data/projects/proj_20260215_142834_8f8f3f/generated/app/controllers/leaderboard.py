from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from app.models.leaderboard import LeaderboardEntry, db

leaderboard_bp = Blueprint('leaderboard', __name__)

@leaderboard_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    try:
        leaderboard_entries = LeaderboardEntry.query.order_by(LeaderboardEntry.score.desc()).all()
        result = [
            {
                'user_id': entry.user_id,
                'username': entry.username,
                'score': entry.score
            }
            for entry in leaderboard_entries
        ]
        return jsonify(result), 200
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500

@leaderboard_bp.route('/leaderboard/<int:user_id>', methods=['GET'])
def get_user_leaderboard(user_id):
    try:
        entry = LeaderboardEntry.query.filter_by(user_id=user_id).first()
        if entry:
            result = {
                'user_id': entry.user_id,
                'username': entry.username,
                'score': entry.score
            }
            return jsonify(result), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500

@leaderboard_bp.route('/leaderboard', methods=['POST'])
def update_leaderboard():
    data = request.get_json()
    user_id = data.get('user_id')
    username = data.get('username')
    score = data.get('score')

    if not user_id or not username or score is None:
        return jsonify({'error': 'Invalid input'}), 400

    try:
        entry = LeaderboardEntry.query.filter_by(user_id=user_id).first()
        if entry:
            entry.username = username
            entry.score = score
        else:
            entry = LeaderboardEntry(user_id=user_id, username=username, score=score)
            db.session.add(entry)
        
        db.session.commit()
        return jsonify({'message': 'Leaderboard updated successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500