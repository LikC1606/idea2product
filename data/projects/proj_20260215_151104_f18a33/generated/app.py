from flask import Flask
from routes import register_routes

def create_app():
    app = Flask(__name__)
    
    # Register all routes from the routes module
    register_routes(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)