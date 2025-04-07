import logging
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from logging.config import dictConfig

# Database ORM: Provides object-relational mapping for interacting with the database.
db: SQLAlchemy = SQLAlchemy()

# Database Migrations: Handles database schema changes over time.
# Requires `flask db init`, `flask db migrate`, `flask db upgrade` commands.
migrate: Migrate = Migrate()

# API Rate Limiting: Protects the API from abuse by limiting request frequency.
# Uses the client's remote IP address as the default key.
# Limits are primarily defined in the application configuration (config.py).
limiter: Limiter = Limiter(key_func=get_remote_address)

# Cross-Origin Resource Sharing: Allows the frontend (on a different domain)
# to make requests to this backend API.
# Configuration (allowed origins) is typically set in config.py.
cors: CORS = CORS()


def configure_logging(app):
    """Configures application logging based on the Flask app config."""
    log_config = app.config.get("LOGGING_CONFIG")
    if log_config:
        # Ensure LOG_LEVEL from general config overrides the default in LOGGING_CONFIG
        log_level = app.config.get("LOG_LEVEL", "INFO").upper()
        log_config["handlers"]["default"]["level"] = log_level
        log_config["loggers"][""]["level"] = log_level
        dictConfig(log_config)
    else:
        # Fallback to basic logging if LOGGING_CONFIG is missing
        logging.basicConfig(
            level=app.config.get("LOG_LEVEL", "INFO").upper(),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
