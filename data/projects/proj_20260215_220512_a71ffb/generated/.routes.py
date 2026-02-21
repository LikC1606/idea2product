from app.controllers.note_controller import note_controller
from app.controllers.user_controller import user_controller

def register_blueprints(app):
    app.register_blueprint(note_controller)
    app.register_blueprint(user_controller)