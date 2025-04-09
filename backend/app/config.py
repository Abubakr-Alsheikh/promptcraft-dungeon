import os
import logging
import logging.config

# Calculate basedir relative to the *project root* (backend/) assuming config.py is in backend/app/
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
instance_path = os.path.join(basedir, "instance")
temp_path = os.path.join(basedir, "temp")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "a_very_secret_key_for_dev")
    DEBUG = False
    TESTING = False

    # Rate Limiting (using Flask-Limiter)
    RATE_LIMIT = os.environ.get(
        "RATE_LIMIT", "5 per minute"
    )  # Default for specific routes
    DEFAULT_RATE_LIMITS = os.environ.get(
        "DEFAULT_RATE_LIMITS", "200 per day;50 per hour"
    ).split(";")

    # CORS Configuration (using Flask-CORS)
    # Allow requests from the Next.js frontend development server and production domains
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

    USE_TEMP_DB = os.environ.get("USE_TEMP_DB", "false").lower() in (
        "true",
        "1",
        "t",
    )

    # Define database URIs
    TEMP_DB_PATH = os.path.join(temp_path, "temp_app.db")
    INSTANCE_DB_PATH = os.path.join(instance_path, "app.db")

    if USE_TEMP_DB:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{TEMP_DB_PATH}"
        print(
            f"INFO: USE_TEMP_DB is True. Using temporary database: {SQLALCHEMY_DATABASE_URI}"
        )
    else:
        # Default to SQLite in the instance folder if DATABASE_URL is not set
        SQLALCHEMY_DATABASE_URI = os.environ.get(
            "DATABASE_URL", f"sqlite:///{INSTANCE_DB_PATH}"
        )
        if "DATABASE_URL" in os.environ:
            print(
                f"INFO: USE_TEMP_DB is False. Using DATABASE_URL: {SQLALCHEMY_DATABASE_URI}"
            )
        else:
            print(
                f"INFO: USE_TEMP_DB is False. Using instance database: {SQLALCHEMY_DATABASE_URI}"
            )
    # --- End New Database Logic ---

    @staticmethod
    def init_app(app):
        # Apply logging configuration from the class
        # Note: Specific configs like DevelopmentConfig might override this later
        log_level = app.config.get("LOG_LEVEL", Config.LOG_LEVEL)
        Config.LOGGING_CONFIG["handlers"]["default"]["level"] = log_level
        Config.LOGGING_CONFIG["loggers"][""]["level"] = log_level
        if app.config.get("SQLALCHEMY_ECHO"):  # Check effective config for echo
            Config.LOGGING_CONFIG["loggers"]["sqlalchemy.engine"]["level"] = "DEBUG"
        else:
            Config.LOGGING_CONFIG["loggers"]["sqlalchemy.engine"]["level"] = "INFO"

        logging.config.dictConfig(Config.LOGGING_CONFIG)
        app.logger.info(
            f"Logging configured at level: {log_level}"
        )  # Use app.logger after config

        # Ensure the correct folder exists based on DB choice
        db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
        use_temp_db = app.config.get("USE_TEMP_DB", False)

        if use_temp_db and db_uri.startswith("sqlite:///"):
            target_dir = temp_path
            db_type_msg = f"temporary database in {target_dir}"
        elif not use_temp_db and db_uri.startswith(f"sqlite:///{instance_path}"):
            target_dir = instance_path
            db_type_msg = f"instance database in {target_dir}"
        else:
            target_dir = None  # Using DATABASE_URL or memory db
            if "sqlite:///:memory:" in db_uri:
                db_type_msg = "in-memory SQLite database"
            elif "DATABASE_URL" in os.environ and not use_temp_db:
                db_type_msg = f"database from DATABASE_URL ({db_uri.split('@')[0]}...)"  # Obfuscate credentials
            else:
                db_type_msg = f"database configured at {db_uri}"  # Fallback message

        if target_dir and not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir)
                app.logger.info(f"Created directory for database: {target_dir}")
            except OSError as e:
                app.logger.error(f"Failed to create directory {target_dir}: {e}")

        # Log the final database and AI configuration
        app.logger.info(f"Using {db_type_msg}")
        app.logger.info(
            f"AI Service: {'Local Ollama' if app.config['USE_LOCAL'] else 'Google Gemini'}{' preferred' if app.config['USE_LOCAL'] else ''}"
        )


class DevelopmentConfig(Config):
    DEBUG = True
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    LOG_LEVEL = "DEBUG"
    SQLALCHEMY_ECHO = True
    DEFAULT_RATE_LIMITS = ["1000 per day", "100 per hour", "20 per minute"]

    @classmethod
    def init_app(cls, app):
        # Call parent init_app first to set up base logging, folders etc.
        super().init_app(app)
        # Development specific messages/overrides can go here
        app.logger.info("Development configuration adjustments applied.")


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = os.environ.get("SECRET_KEY", "test-secret-key")
    # Override SQLALCHEMY_DATABASE_URI regardless of USE_TEMP_DB for tests
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ECHO = False
    WTF_CSRF_ENABLED = False
    DEBUG = True  # Often helpful
    LOG_LEVEL = "DEBUG"
    DEFAULT_RATE_LIMITS = []
    RATE_LIMIT_ENABLED = False
    # Override USE_TEMP_DB to avoid side effects during testing
    USE_TEMP_DB = False

    @classmethod
    def init_app(cls, app):
        # Don't call parent init_app if we don't want folder creation etc. for memory DB
        # However, we might still want basic logging setup from parent
        super().init_app(app)
        app.config["SQLALCHEMY_DATABASE_URI"] = cls.SQLALCHEMY_DATABASE_URI
        app.logger.info("Testing configuration loaded (using in-memory DB).")


class ProductionConfig(Config):
    LOG_LEVEL = "INFO"  # Or WARNING/ERROR
    SQLALCHEMY_ECHO = False
    DEBUG = False

    @classmethod
    def init_app(cls, app):
        # Call parent init_app first
        super().init_app(app)

        # Production environment sanity checks
        # These checks should ideally use app.config to check the *effective* values
        if (
            not app.config.get("SECRET_KEY")
            or app.config["SECRET_KEY"] == "a_very_secret_key_for_dev"
            or app.config["SECRET_KEY"] == "dev-secret-key"
        ):
            # Use app.logger for consistency, but raise error to halt startup
            app.logger.critical(
                "CRITICAL: Production SECRET_KEY is not set or is insecure."
            )
            raise ValueError(
                "CRITICAL: Production SECRET_KEY is not set or is insecure."
            )

        # Check if using temp DB in production (might be undesirable)
        if app.config.get("USE_TEMP_DB"):
            app.logger.warning(
                "WARNING: USE_TEMP_DB is enabled in production. Ensure this is intended."
            )
        # Check if using default instance SQLite in production
        elif (
            app.config["SQLALCHEMY_DATABASE_URI"]
            == f"sqlite:///{Config.INSTANCE_DB_PATH}"
        ):
            app.logger.warning(
                "WARNING: Using default instance SQLite database in production is not recommended. Set DATABASE_URL to a robust database like PostgreSQL."
            )

        if not app.config.get("GEMINI_API_KEY") and not app.config.get("USE_LOCAL"):
            app.logger.warning(
                "WARNING: GEMINI_API_KEY is not set, and USE_LOCAL is false. AI fallback might not be available."
            )
        app.logger.info("Production configuration adjustments applied.")


# Dictionary to easily access configuration classes by name
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
