import logging
from flask import Flask

# Import configuration mapping
from .config import config

# Import extension instances and logging configurator
from .extensions import db, migrate, limiter, cors, configure_logging

# Import registration functions
from .routes import register_blueprints
from .utils.error_handlers import register_error_handlers

# Get the root logger configured by dictConfig
log = logging.getLogger(__name__)  # Use standard logging instance


def create_app(config_name: str = "development") -> Flask:
    """
    Application Factory Pattern: Creates and configures the Flask application.

    Args:
        config_name (str): The configuration profile to use (e.g., "development", "production", "testing").

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(
        __name__, instance_relative_config=True
    )  # Enable instance folder config loading if needed

    # --- 1. Load Configuration ---
    selected_config = config.get(config_name)
    if not selected_config:
        raise ValueError(
            f"Invalid FLASK_CONFIG: '{config_name}'. Check available configs in config.py"
        )

    app.config.from_object(selected_config)
    # Allow overriding config with instance/config.py (if it exists and needed)
    # app.config.from_pyfile('config.py', silent=True)

    # Perform config-specific initialization (e.g., creating instance folder)
    if hasattr(selected_config, "init_app"):
        selected_config.init_app(app)

    # --- 2. Configure Logging ---
    # Setup logging based on the loaded configuration BEFORE initializing extensions
    # that might log during setup.
    configure_logging(app)
    log.info(f"Flask application configured with '{config_name}' profile.")
    log.debug(f"Debug mode: {app.debug}")

    # --- 3. Initialize Flask Extensions ---
    log.debug("Initializing Flask extensions...")
    # Database ORM
    db.init_app(app)
    log.debug(f"Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not Set')}")
    # Database Migrations (requires db)
    migrate.init_app(app, db)
    # API Rate Limiting
    limiter.init_app(app)
    # Cross-Origin Resource Sharing (CORS)
    # Configuration (origins, credentials support) is pulled from app.config
    cors.init_app(app)
    log.debug(f"CORS configured for origins: {app.config.get('CORS_ORIGINS')}")
    log.debug("Extensions initialized.")

    # --- 4. Register Blueprints (API Routes) ---
    log.debug("Registering blueprints...")
    register_blueprints(app)
    log.debug("Blueprints registered.")

    # --- 5. Register Error Handlers ---
    log.debug("Registering error handlers...")
    register_error_handlers(
        app
    )  # Ensure this function exists and is correctly implemented
    log.debug("Error handlers registered.")

    # --- 6. Development/Testing Convenience: Create DB Tables ---
    # WARNING: db.create_all() should NOT be relied upon for production schema management
    #          when using Flask-Migrate/Alembic. Use 'flask db upgrade' instead.
    #          This is primarily for initial setup in dev/test or with SQLite where migrations might be skipped.
    if app.config.get("SQLALCHEMY_DATABASE_URI", "").startswith("sqlite"):
        with app.app_context():
            log.debug("Attempting db.create_all() for SQLite development setup...")
            try:
                db.create_all()
                log.info(
                    "db.create_all() completed (useful for initial SQLite setup/testing)."
                )
            except Exception as e:
                log.error(f"Error during db.create_all(): {e}", exc_info=True)
    else:
        log.info(
            "Skipping db.create_all() (likely using PostgreSQL/MySQL with migrations). Use 'flask db upgrade'."
        )

    # --- 7. Application Context ---
    # Example: Log routes if in debug mode
    if app.debug:
        with app.app_context():
            log.debug("Registered URL Rules:")
            for rule in app.url_map.iter_rules():
                log.debug(
                    f"- {rule.endpoint}: {rule.rule} Methods: {','.join(rule.methods)}"
                )

    # --- Final Log Message ---
    log.info(
        f"AI Service Preference: {'Local Ollama' if app.config.get('USE_LOCAL') else 'Cloud (Gemini)'}"
    )
    if app.config.get("USE_LOCAL"):
        log.info(f"Ollama URL: {app.config.get('OLLAMA_URL')}")
    log.info("Flask application creation complete.")

    return app
