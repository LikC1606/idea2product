from app import create_app

# Main entry point
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)