from app.models.problem import Problem

def get_all_problems():
    """
    Retrieve all problems from the database.
    
    Returns:
        list: A list of Problem objects.
    """
    # Assuming Problem.query.all() fetches all problems from the database
    return Problem.query.all()