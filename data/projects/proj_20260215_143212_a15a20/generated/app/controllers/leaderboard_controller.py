from flask import Blueprint, jsonify, request
from sqlalchemy.orm import Session
from app.models.leaderboard import Leaderboard
from app.database import get_db

leaderboard_bp = Blueprint('leaderboard', __name__)

@leaderboard_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    db: Session = get_db()
    try:
        leaderboard_entries = db.query(Leaderboard).order_by(Leaderboard.score.desc()).all()
        return jsonify([entry.to_dict() for entry in leaderboard_entries]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@leaderboard_bp.route('/leaderboard/<int:user_id>', methods=['GET'])
def get_user_leaderboard_entry(user_id):
    db: Session = get_db()
    try:
        entry = db.query(Leaderboard).filter(Leaderboard.user_id == user_id).first()
        if entry:
            return jsonify(entry.to_dict()), 200
        else:
            return jsonify({'error': 'User not found in leaderboard'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@leaderboard_bp.route('/leaderboard', methods=['POST'])
def add_leaderboard_entry():
    db: Session = get_db()
    data = request.json
    try:
        new_entry = Leaderboard(user_id=data['user_id'], score=data['score'])
        db.add(new_entry)
        db.commit()
        return jsonify(new_entry.to_dict()), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

@leaderboard_bp.route('/leaderboard/<int:user_id>', methods=['PUT'])
def update_leaderboard_entry(user_id):
    db: Session = get_db()
    data = request.json
    try:
        entry = db.query(Leaderboard).filter(Leaderboard.user_id == user_id).first()
        if entry:
            entry.score = data.get('score', entry.score)
            db.commit()
            return jsonify(entry.to_dict()), 200
        else:
            return jsonify({'error': 'User not found in leaderboard'}), 404
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

@leaderboard_bp.route('/leaderboard/<int:user_id>', methods=['DELETE'])
def delete_leaderboard_entry(user_id):
    db: Session = get_db()
    try:
        entry = db.query(Leaderboard).filter(Leaderboard.user_id == user_id).first()
        if entry:
            db.delete(entry)
            db.commit()
            return jsonify({'message': 'Entry deleted successfully'}), 200
        else:
            return jsonify({'error': 'User not found in leaderboard'}), 404
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500