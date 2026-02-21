from flask import Flask
from routes import register_routes

# Initialize the Flask application
app = Flask(__name__)

# Register routes from the routes module
register_routes(app)

# Entry point for the application
if __name__ == '__main__':
    app.run(debug=True)