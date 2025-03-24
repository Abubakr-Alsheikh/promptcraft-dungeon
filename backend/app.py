from flask import Flask, jsonify
from flask_cors import CORS
from routes.game_routes import game_bp
from config import Config
from extensions import limiter
import logging


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    limiter.init_app(app)

    # Register blueprints
    app.register_blueprint(game_bp, url_prefix="/api/game")

    # Configure logging
    logging.basicConfig(level=app.config["LOG_LEVEL"])

    # Error handling
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return (
            jsonify(
                {
                    "error": "Rate limit exceeded",
                    "message": "Please wait before making another request",
                }
            ),
            429,
        )

    @app.errorhandler(500)
    def internal_error(e):
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "An unexpected error occurred",
                }
            ),
            500,
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(port=5001)
