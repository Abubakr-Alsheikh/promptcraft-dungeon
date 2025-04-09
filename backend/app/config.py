import os
import logging
import logging.config

# Calculate basedir relative to the *project root* (backend/) assuming config.py is in backend/app/
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
instance_path = os.path.join(basedir, "instance")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "a_very_secret_key_for_dev")
    DEBUG = False
    TESTING = False

    # Rate Limiting (using Flask-Limiter)
    RATE_LIMIT = os.environ.get("RATE_LIMIT", "5 per minute")
    DEFAULT_RATE_LIMITS = os.environ.get(
        "DEFAULT_RATE_LIMITS", "200 per day;50 per hour"
    ).split(";")

    # CORS Configuration (using Flask-CORS)
    CORS_ORIGINS = os.environ.get(
        "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    CORS_SUPPORTS_CREDENTIALS = True

    # AI Service Configuration
    OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    USE_LOCAL = os.environ.get("USE_LOCAL", "false").lower() in (
        "true",
        "1",
        "t",
    )
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "deepseek-r1:1.5B")
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    AI_REQUEST_TIMEOUT = int(os.environ.get("AI_REQUEST_TIMEOUT", 60))

    # Logging Configuration
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            },
        },
        "handlers": {
            "default": {
                "level": LOG_LEVEL,
                "formatter": "standard",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "": {
                "handlers": ["default"],
                "level": LOG_LEVEL,
                "propagate": True,
            },
            "werkzeug": {"propagate": True},
            "sqlalchemy.engine": {
                "level": "INFO",
                "propagate": False,
            },
        },
    }
    # Database Configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # Connection pool settings (useful for production with Postgres/Neon)
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,  # Recycle slightly faster than 5 min Neon idle timeout
        "pool_pre_ping": True,  # Check connection validity before use
    }

    # Define database URI
    # Priority: DATABASE_URL environment variable.
    # Fallback: SQLite database in the instance folder (for simple local dev setup).
    INSTANCE_DB_PATH = os.path.join(instance_path, "app.db")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{INSTANCE_DB_PATH}"
    )
    # Removed USE_TEMP_DB logic

    @staticmethod
    def init_app(app):
        """Initialize application-specific settings."""
        # Apply logging configuration dynamically based on effective config
        log_level = app.config.get(
            "LOG_LEVEL", Config.LOG_LEVEL
        )  # Use effective LOG_LEVEL
        # Update handler and root logger level in the template dict
        Config.LOGGING_CONFIG["handlers"]["default"]["level"] = log_level
        Config.LOGGING_CONFIG["loggers"][""]["level"] = log_level

        # Set SQLAlchemy engine log level based on effective SQLALCHEMY_ECHO
        if app.config.get("SQLALCHEMY_ECHO"):
            Config.LOGGING_CONFIG["loggers"]["sqlalchemy.engine"]["level"] = "DEBUG"
        else:
            Config.LOGGING_CONFIG["loggers"]["sqlalchemy.engine"]["level"] = "INFO"

        # Apply the configured logging settings
        logging.config.dictConfig(Config.LOGGING_CONFIG)
        # Use app.logger *after* config is applied
        app.logger.info(f"Logging configured at level: {log_level}")

        # --- Determine and Log Database Configuration ---
        db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
        target_dir = None
        db_type_msg = ""

        # Check if we are using the default SQLite path
        if db_uri == f"sqlite:///{app.config['INSTANCE_DB_PATH']}":
            target_dir = instance_path
            db_type_msg = f"default instance SQLite database in {target_dir}"
        # Check if we are using any other SQLite file path
        elif db_uri.startswith("sqlite:///"):
            # Extract path if possible, handle relative/absolute paths
            path_part = db_uri[len("sqlite///") :]
            if not os.path.isabs(path_part):
                path_part = os.path.join(
                    basedir, path_part
                )  # Assume relative to basedir if not absolute
            target_dir = os.path.dirname(path_part)
            db_type_msg = f"SQLite database file at {path_part}"
        # Check if using in-memory SQLite (primarily for testing)
        elif "sqlite:///:memory:" in db_uri:
            db_type_msg = "in-memory SQLite database"
        # Check if DATABASE_URL was likely used (Postgres, MySQL etc.)
        elif "DATABASE_URL" in os.environ and db_uri == os.environ["DATABASE_URL"]:
            # Obfuscate credentials if present
            safe_uri = db_uri.split("@")[-1]  # Show host/db part
            db_type_msg = f"database from DATABASE_URL (connecting to {safe_uri})"
        # Fallback message
        else:
            db_type_msg = f"database configured at {db_uri}"

        # Create instance folder only if using the default instance SQLite DB
        if target_dir == instance_path and not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir)
                app.logger.info(
                    f"Created instance directory for database: {target_dir}"
                )
            except OSError as e:
                app.logger.error(
                    f"Failed to create instance directory {target_dir}: {e}"
                )
        elif (
            target_dir
            and target_dir != instance_path
            and not os.path.exists(target_dir)
        ):
            app.logger.warning(
                f"Target directory for SQLite DB does not exist: {target_dir}. Database creation might fail if path is invalid."
            )

        app.logger.info(f"Using {db_type_msg}")

        # Log AI configuration
        app.logger.info(
            f"AI Service: {'Local Ollama' if app.config['USE_LOCAL'] else 'Google Gemini'}{' preferred' if app.config['USE_LOCAL'] else ''}"
        )


class DevelopmentConfig(Config):
    DEBUG = True
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    LOG_LEVEL = "DEBUG"
    SQLALCHEMY_ECHO = True  # Show SQL queries in development
    DEFAULT_RATE_LIMITS = [
        "1000 per day",
        "100 per hour",
        "20 per minute",
    ]  # Relaxed limits for dev

    @classmethod
    def init_app(cls, app):
        # Set effective config values before calling parent init_app
        app.config["LOG_LEVEL"] = cls.LOG_LEVEL
        app.config["SQLALCHEMY_ECHO"] = cls.SQLALCHEMY_ECHO
        super().init_app(app)  # Call base init_app to apply logging, log messages etc.
        app.logger.info(
            "Development configuration adjustments applied (DEBUG=True, SQLALCHEMY_ECHO=True)."
        )


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SECRET_KEY = os.environ.get("SECRET_KEY", "test-secret-key")
    # Force in-memory SQLite database for isolated tests
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ECHO = False
    WTF_CSRF_ENABLED = False
    LOG_LEVEL = "DEBUG"
    DEFAULT_RATE_LIMITS = []
    RATE_LIMIT_ENABLED = False
    # Ensure pooling options don't interfere with in-memory DB if they somehow get applied
    SQLALCHEMY_ENGINE_OPTIONS = {}

    @classmethod
    def init_app(cls, app):
        # Set effective config values before calling parent init_app
        app.config["SQLALCHEMY_DATABASE_URI"] = cls.SQLALCHEMY_DATABASE_URI
        app.config["LOG_LEVEL"] = cls.LOG_LEVEL
        app.config["SQLALCHEMY_ECHO"] = cls.SQLALCHEMY_ECHO
        app.config["TESTING"] = cls.TESTING
        app.config["DEBUG"] = cls.DEBUG
        super().init_app(app)  # Call base init_app
        app.logger.info("Testing configuration loaded (using in-memory SQLite DB).")


class ProductionConfig(Config):
    LOG_LEVEL = "INFO"  # Standard level for production
    SQLALCHEMY_ECHO = False  # Never echo SQL in production
    DEBUG = False

    @classmethod
    def init_app(cls, app):
        # Set effective config values before calling parent init_app
        app.config["LOG_LEVEL"] = cls.LOG_LEVEL
        app.config["SQLALCHEMY_ECHO"] = cls.SQLALCHEMY_ECHO
        app.config["DEBUG"] = cls.DEBUG
        super().init_app(app)  # Call base init_app

        # --- Production Sanity Checks ---
        # Check effective SECRET_KEY
        secret_key = app.config.get("SECRET_KEY")
        if not secret_key or secret_key in (
            "a_very_secret_key_for_dev",
            "dev-secret-key",
        ):
            app.logger.critical(
                "CRITICAL: Production SECRET_KEY is not set or is insecure."
            )
            raise ValueError("Production SECRET_KEY is not set or is insecure.")

        # Check if using the default instance SQLite (not recommended for production)
        if (
            app.config["SQLALCHEMY_DATABASE_URI"]
            == f"sqlite:///{Config.INSTANCE_DB_PATH}"
        ):
            app.logger.warning(
                "WARNING: Using default instance SQLite database in production is not recommended. "
                "Set the DATABASE_URL environment variable to a robust database (e.g., PostgreSQL)."
            )
        elif app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:///"):
            app.logger.warning(
                "WARNING: Using a file-based SQLite database in production can have limitations "
                "regarding concurrency and backups. Consider PostgreSQL or MySQL via DATABASE_URL."
            )

        # Check AI key if not using local AI
        if not app.config.get("USE_LOCAL") and not app.config.get("GEMINI_API_KEY"):
            app.logger.warning(
                "WARNING: Production is configured to use Cloud AI (USE_LOCAL=False), "
                "but GEMINI_API_KEY is not set. AI features may fail."
            )

        app.logger.info("Production configuration adjustments applied.")


# Dictionary to easily access configuration classes by name
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,  # Default to development if FLASK_CONFIG is not set
}
