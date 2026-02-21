from app.models.user import User, get_user
from app.database import db_session

class UserController:
    @staticmethod
    def get_user_profile(user_id):
        """
        Retrieve user profile information by user ID.
        
        :param user_id: ID of the user
        :return: User object or None if not found
        """
        user = get_user(user_id)
        return user

    @staticmethod
    def update_user_profile(user_id, **kwargs):
        """
        Update user profile information.

        :param user_id: ID of the user to update
        :param kwargs: Dictionary of fields to update
        :return: Updated User object or None if user not found
        """
        user = get_user(user_id)
        if not user:
            return None

        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        db_session.commit()
        return user

    @staticmethod
    def delete_user(user_id):
        """
        Delete a user profile by user ID.

        :param user_id: ID of the user to delete
        :return: Boolean indicating success of the operation
        """
        user = get_user(user_id)
        if not user:
            return False

        db_session.delete(user)
        db_session.commit()
        return True