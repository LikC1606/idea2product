# app/controllers/leaderboard_controller.py

from app.models.leaderboard import Leaderboard, get_leaderboard
from app.models.problem import Problem, get_problem
from app.models.user import User, get_user
from app.database import db_session

def get_leaderboard_data(problem_id):
    """
    Fetches leaderboard data for a specific problem.

    Args:
        problem_id (int): ID of the problem.

    Returns:
        list[dict]: List of leaderboard entries with user and score details.
    """
    try:
        # Validate problem existence
        problem = get_problem(problem_id)
        if not problem:
            raise ValueError(f"Problem with ID {problem_id} does not exist.")

        # Fetch leaderboard entries for the problem
        leaderboard_entries = (
            db_session.query(Leaderboard)
            .filter(Leaderboard.problem_id == problem_id)
            .order_by(Leaderboard.score.desc())
            .all()
        )

        # Format leaderboard entries
        formatted_entries = []
        for entry in leaderboard_entries:
            user = get_user(entry.user_id)
            if user:
                formatted_entries.append({
                    "username": user.username,
                    "score": entry.score,
                    "submission_time": entry.submission_time
                })

        return formatted_entries

    except Exception as e:
        raise RuntimeError(f"Error fetching leaderboard data: {str(e)}")

def update_leaderboard(problem_id, user_id, score):
    """
    Updates the leaderboard with a new score for a given user and problem.

    Args:
        problem_id (int): ID of the problem.
        user_id (int): ID of the user.
        score (int): New score to be recorded.

    Returns:
        dict: Updated leaderboard entry.
    """
    try:
        # Validate problem existence
        problem = get_problem(problem_id)
        if not problem:
            raise ValueError(f"Problem with ID {problem_id} does not exist.")

        # Validate user existence
        user = get_user(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} does not exist.")

        # Check if there's an existing leaderboard entry
        existing_entry = (
            db_session.query(Leaderboard)
            .filter(Leaderboard.problem_id == problem_id, Leaderboard.user_id == user_id)
            .first()
        )

        if existing_entry:
            # Update score if new score is higher
            if score > existing_entry.score:
                existing_entry.score = score
                db_session.commit()
        else:
            # Create new leaderboard entry
            new_entry = Leaderboard(
                problem_id=problem_id,
                user_id=user_id,
                score=score
            )
            db_session.add(new_entry)
            db_session.commit()

        return {
            "problem_id": problem_id,
            "user_id": user_id,
            "score": score
        }

    except Exception as e:
        raise RuntimeError(f"Error updating leaderboard: {str(e)}")

# Must Export
__all__ = ["get_leaderboard_data", "update_leaderboard"]