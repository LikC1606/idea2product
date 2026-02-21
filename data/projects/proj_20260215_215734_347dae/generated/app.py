from app import create_app

# Entry point for running the Flask application
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)