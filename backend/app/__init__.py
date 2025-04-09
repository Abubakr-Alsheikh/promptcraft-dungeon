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
        config_name (str): The configuration profile to use ('development', 'production', 'testing').

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(
        __name__, instance_relative_config=True
    )  # Enable instance folder config loading if needed

    # --- 1. Load Configuration ---
    selected_config = config.get(config_name)
    if not selected_config:
        # Fallback to default if invalid config_name provided, or raise error
        log.warning(
            f"Invalid FLASK_CONFIG '{config_name}'. Falling back to 'default' ({config['default'].__name__})."
        )
        selected_config = config["default"]
        config_name = "default"  # Update config_name to reflect the actual config used

    app.config.from_object(selected_config)

    # --- 2. Configure Logging (using effective config) ---
    # Logging setup now happens *after* config is loaded but *before* extensions init
    configure_logging(app)  # Pass the app to use its effective config
    log.info(f"Flask application configured with '{config_name}' profile.")
    log.debug(f"Debug mode: {app.debug}")
    log.debug(f"Testing mode: {app.testing}")

    # --- 3. Initialize Flask Extensions ---
    log.debug("Initializing Flask extensions...")
    # Database ORM
    db.init_app(app)
    # Use app.logger for logging after configure_logging has run
    app.logger.debug(
        f"Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not Set')}"
    )
    if app.config.get("SQLALCHEMY_ENGINE_OPTIONS"):
        app.logger.debug(
            f"SQLAlchemy Engine Options: {app.config['SQLALCHEMY_ENGINE_OPTIONS']}"
        )
    # Database Migrations (requires db)
    migrate.init_app(app, db)
    # API Rate Limiting
    limiter.init_app(app)
    # Cross-Origin Resource Sharing (CORS)
    cors.init_app(
        app,
        supports_credentials=app.config.get("CORS_SUPPORTS_CREDENTIALS", False),
        origins=app.config.get("CORS_ORIGINS", []),
    )
    app.logger.debug(f"CORS configured for origins: {app.config.get('CORS_ORIGINS')}")
    log.debug("Extensions initialized.")

    # --- 4. Initialize Base Application Settings (like folder creation via Config.init_app) ---
    # Moved this *after* extension init, especially db init, but before create_all
    # Config.init_app takes care of logging DB type and creating instance folder if needed
    if hasattr(selected_config, "init_app"):
        selected_config.init_app(app)

    # --- 5. Register Blueprints (API Routes) ---
    log.debug("Registering blueprints...")
    register_blueprints(app)
    log.debug("Blueprints registered.")

    # --- 6. Register Error Handlers ---
    log.debug("Registering error handlers...")
    register_error_handlers(app)
    log.debug("Error handlers registered.")

    # --- 7. Create DB Tables (Development/Testing ONLY) ---
    # **NEVER rely on this in Production.** Use `flask db upgrade` for schema management.
    if config_name in ("development", "testing"):
        with app.app_context():
            app.logger.info(
                f"Running in '{config_name}' mode. Attempting db.create_all() for initial setup/testing."
            )
            try:
                # Reflect checks if tables exist before creating, safe to run multiple times
                # but doesn't handle migrations (column changes etc.)
                db.create_all()
                app.logger.info(
                    "db.create_all() completed. Remember to use 'flask db migrate/upgrade' for schema changes."
                )
            except Exception as e:
                # Log error, but don't necessarily stop app start. DB might be partially ready or connection failed.
                app.logger.error(f"Error during db.create_all(): {e}", exc_info=True)
                app.logger.error(
                    "Database tables might not be fully created or updated."
                )
    else:  # Production or other custom configs
        app.logger.info(
            f"Running in '{config_name}' mode. Skipping db.create_all(). "
            "Database schema MUST be managed using Flask-Migrate ('flask db upgrade')."
        )

    # --- 8. Application Context / Final Setup ---
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
