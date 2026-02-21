from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    """
    Hash a plaintext password using Werkzeug's security utilities.

    Args:
        password (str): The plaintext password to hash.

    Returns:
        str: The hashed password.
    """
    return generate_password_hash(password)

def check_password(hashed_password, password):
    """
    Verify a plaintext password against its hashed counterpart.

    Args:
        hashed_password (str): The hashed password.
        password (str): The plaintext password to verify.

    Returns:
        bool: True if the password matches the hash, False otherwise.
    """
    return check_password_hash(hashed_password, password)