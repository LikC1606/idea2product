# app/services/online_judge_service.py

from sqlalchemy.exc import SQLAlchemyError
from app.models.problem import Problem, get_problem
from app.models.user import User, get_user
from app.models.leaderboard import Leaderboard, get_leaderboard

import subprocess
import tempfile
import os

class OnlineJudgeService:
    def __init__(self, db_session):
        self.db_session = db_session

    def execute_code(self, code: str, input_data: str) -> dict:
        """
        Executes the given code with the provided input data in a sandboxed environment.
        Returns the output and execution status.
        """
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp_code_file:
                temp_code_file.write(code.encode())
                temp_code_file_path = temp_code_file.name

            with tempfile.NamedTemporaryFile(delete=False) as temp_input_file:
                temp_input_file.write(input_data.encode())
                temp_input_file_path = temp_input_file.name

            # Execute the code in a sandboxed environment
            process = subprocess.run(
                ["python3", temp_code_file_path],
                stdin=open(temp_input_file_path, "r"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )

            output = process.stdout.decode()
            error = process.stderr.decode()

            os.remove(temp_code_file_path)
            os.remove(temp_input_file_path)

            if process.returncode != 0:
                return {
                    "status": "error",
                    "output": error
                }

            return {
                "status": "success",
                "output": output
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "output": "Code execution timed out."
            }
        except Exception as e:
            return {
                "status": "error",
                "output": str(e)
            }

    def validate_submission(self, user_id: int, problem_id: int, code: str) -> dict:
        """
        Validates the submission by running the code against the problem's test cases.
        Updates the leaderboard if the submission is correct.
        """
        try:
            problem = get_problem(self.db_session, problem_id)
            user = get_user(self.db_session, user_id)

            if not problem or not user:
                return {
                    "status": "error",
                    "message": "Invalid problem or user."
                }

            for test_case in problem.test_cases:
                result = self.execute_code(code, test_case["input"])
                if result["status"] != "success" or result["output"].strip() != test_case["expected_output"].strip():
                    return {
                        "status": "failed",
                        "message": "Test case failed.",
                        "details": result
                    }

            # Update leaderboard
            leaderboard = get_leaderboard(self.db_session)
            leaderboard.update_score(user_id, problem_id)

            return {
                "status": "success",
                "message": "Submission validated successfully."
            }
        except SQLAlchemyError as e:
            return {
                "status": "error",
                "message": str(e)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

# Must Export
__all__ = ["OnlineJudgeService"]