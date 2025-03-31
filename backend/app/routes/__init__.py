# backend/app/routes/__init__.py
from flask import Blueprint


def register_blueprints(app):
    from .game_routes import game_bp

    # Import other blueprints here if you add them (e.g., auth_bp)

    app.register_blueprint(game_bp, url_prefix="/api/game")
    # app.register_blueprint(auth_bp, url_prefix='/api/auth')
