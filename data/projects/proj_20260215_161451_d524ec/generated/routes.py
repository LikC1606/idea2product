from flask import Blueprint, jsonify

# Blueprint for API routes
routes = Blueprint('routes', __name__)

@routes.route('/api/status', methods=['GET'])
def api_status():
    """
    API endpoint to check the status of the application.
    """
    return jsonify({"status": "OK", "message": "ACM Problem-Solving Platform is running successfully."})

# Export the blueprint
__all__ = ['routes']