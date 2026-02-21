from flask import jsonify

def handle_404(error: Exception):
    response = {
        "error": "Not Found",
        "message": "The requested resource could not be found."
    }
    return jsonify(response), 404