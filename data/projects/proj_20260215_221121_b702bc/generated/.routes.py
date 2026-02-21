from flask import Blueprint
from app.controllers.note_controller import note_controller
from app.controllers.category_controller import category_controller

def register_blueprints(app):
    app.register_blueprint(note_controller)
    app.register_blueprint(category_controller)