from app import create_app

# Entry point for the ACM Problem-Solving Platform
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)