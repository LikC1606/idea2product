from sqlalchemy.exc import SQLAlchemyError
from app.models.problem import Problem, get_problem
from app.database import db_session

class ProblemController:
    @staticmethod
    def create_problem(title, description, difficulty):
        """
        Create a new problem.
        """
        try:
            new_problem = Problem(title=title, description=description, difficulty=difficulty)
            db_session.add(new_problem)
            db_session.commit()
            return new_problem
        except SQLAlchemyError as e:
            db_session.rollback()
            raise ValueError(f"Error creating problem: {str(e)}")

    @staticmethod
    def get_problem_by_id(problem_id):
        """
        Retrieve a problem by its ID.
        """
        problem = get_problem(problem_id)
        if not problem:
            raise ValueError(f"Problem with ID {problem_id} not found.")
        return problem

    @staticmethod
    def update_problem(problem_id, title=None, description=None, difficulty=None):
        """
        Update an existing problem's details.
        """
        problem = get_problem(problem_id)
        if not problem:
            raise ValueError(f"Problem with ID {problem_id} not found.")
        try:
            if title:
                problem.title = title
            if description:
                problem.description = description
            if difficulty:
                problem.difficulty = difficulty
            db_session.commit()
            return problem
        except SQLAlchemyError as e:
            db_session.rollback()
            raise ValueError(f"Error updating problem: {str(e)}")

    @staticmethod
    def delete_problem(problem_id):
        """
        Delete a problem by its ID.
        """
        problem = get_problem(problem_id)
        if not problem:
            raise ValueError(f"Problem with ID {problem_id} not found.")
        try:
            db_session.delete(problem)
            db_session.commit()
        except SQLAlchemyError as e:
            db_session.rollback()
            raise ValueError(f"Error deleting problem: {str(e)}")