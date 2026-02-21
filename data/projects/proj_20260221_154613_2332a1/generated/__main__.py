from flask import Flask
from app.routes import index, create_post, upload_image
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register routes
    app.add_url_rule('/', 'index', index)
    app.add_url_rule('/create-post', 'create_post', create_post, methods=['GET', 'POST'])
    app.add_url_rule('/upload-image', 'upload_image', upload_image, methods=['GET', 'POST'])

    return app

def main():
    app = create_app()
    app.run(debug=True)

if __name__ == '__main__':
    main()