import logging
from flask import Flask
from flask_cors import CORS

from .config import config
from .extensions import db, migrate, limiter
from .routes import register_blueprints
from .utils.error_handlers import register_error_handlers


def create_app(config_name="development"):
    """Application Factory Pattern"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)  # Initialize config specific settings

    # Initialize extensions
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )
    limiter.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)  # Initialize Flask-Migrate

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Configure logging
    logging.basicConfig(level=app.config["LOG_LEVEL"])
    app.logger.setLevel(app.config["LOG_LEVEL"])
    app.logger.info(f"App created with config: {config_name}")
    app.logger.info(f"Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    app.logger.info(f"Using Local LLM: {app.config.get('USE_LOCAL')}")
    app.logger.info(f"Ollama URL: {app.config.get('OLLAMA_URL')}")

    # Create DB tables if they don't exist (useful for SQLite)
    # For production with Alembic, you'd use migrations instead.
    with app.app_context():
        db.create_all()  # Make sure tables are created

    return app
