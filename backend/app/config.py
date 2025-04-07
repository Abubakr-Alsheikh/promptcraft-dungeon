import os
import logging

# Calculate basedir relative to the *project root* (backend/) assuming config.py is in backend/app/
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
instance_path = os.path.join(basedir, "instance")


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
    ).split(
        ";"
    )  # Global defaults

    # CORS Configuration (using Flask-CORS)
    # Allow requests from the Next.js frontend development server and production domains
    CORS_ORIGINS = os.environ.get(
        "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    CORS_SUPPORTS_CREDENTIALS = True  # If using cookies/sessions across domains

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
    # Basic logging setup, can be expanded with handlers, formatters etc. in create_app
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
                "stream": "ext://sys.stdout",  # Use stdout
            },
        },
        "loggers": {
            "": {  # root logger
                "handlers": ["default"],
                "level": LOG_LEVEL,
                "propagate": True,
            },
            "werkzeug": {"propagate": True},  # Allow werkzeug logs if needed
            "sqlalchemy.engine": {
                "level": "INFO",
                "propagate": False,
            },  # Control SQLAlchemy logging level
        },
    }

    # Database Configuration
    # Default to SQLite in the instance folder for ease of setup
    # Recommend PostgreSQL for production (set DATABASE_URL env var)
    # Example: postgresql://user:password@host:port/database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(instance_path, 'app.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # For SQL query logging

    @staticmethod
    def init_app(app):
        # Ensure the instance folder exists when the app is initialized
        if not os.path.exists(instance_path):
            try:
                os.makedirs(instance_path)
                app.logger.info(f"Created instance folder at: {instance_path}")
            except OSError as e:
                app.logger.error(
                    f"Failed to create instance folder at {instance_path}: {e}"
                )
        app.logger.info(f"Using database at: {app.config['SQLALCHEMY_DATABASE_URI']}")
        app.logger.info(
            f"AI Service: {'Local Ollama' if app.config['USE_LOCAL'] else 'Google Gemini'}{' preferred' if app.config['USE_LOCAL'] else ''}"
        )


class DevelopmentConfig(Config):
    DEBUG = True
    SECRET_KEY = os.environ.get(
        "SECRET_KEY", "dev-secret-key"
    )  # Use a distinct dev key
    LOG_LEVEL = "DEBUG"
    SQLALCHEMY_ECHO = True
    # Relax rate limits for easier development/testing
    DEFAULT_RATE_LIMITS = ["1000 per day", "100 per hour", "20 per minute"]

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        # Update logging level for development
        cls.LOGGING_CONFIG["handlers"]["default"]["level"] = cls.LOG_LEVEL
        cls.LOGGING_CONFIG["loggers"][""]["level"] = cls.LOG_LEVEL
        logging.config.dictConfig(cls.LOGGING_CONFIG)
        app.logger.info("Development configuration loaded.")


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = os.environ.get("SECRET_KEY", "test-secret-key")
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # Use in-memory SQLite for tests
    SQLALCHEMY_ECHO = False
    WTF_CSRF_ENABLED = False  # Disable CSRF protection in forms for tests
    DEBUG = True  # Often helpful to have debug on during tests
    LOG_LEVEL = "DEBUG"  # Or suppress logging further if desired
    # Disable rate limiting for tests
    DEFAULT_RATE_LIMITS = []
    RATE_LIMIT_ENABLED = False  # Explicitly disable if Flask-Limiter respects this

    @classmethod
    def init_app(cls, app):
        # Don't call Config.init_app as we don't need instance folder for :memory:
        app.logger.info("Testing configuration loaded.")


class ProductionConfig(Config):
    LOG_LEVEL = "INFO"  # Or WARNING/ERROR
    SQLALCHEMY_ECHO = False
    DEBUG = False

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        # Update logging level for production
        cls.LOGGING_CONFIG["handlers"]["default"]["level"] = cls.LOG_LEVEL
        cls.LOGGING_CONFIG["loggers"][""]["level"] = cls.LOG_LEVEL
        logging.config.dictConfig(cls.LOGGING_CONFIG)

        # Production environment sanity checks
        if (
            not Config.SECRET_KEY
            or Config.SECRET_KEY == "a_very_secret_key_for_dev"
            or Config.SECRET_KEY == "dev-secret-key"
        ):
            raise ValueError(
                "CRITICAL: Production SECRET_KEY is not set or is insecure."
            )
        if (
            not Config.SQLALCHEMY_DATABASE_URI
            or "sqlite" in Config.SQLALCHEMY_DATABASE_URI.lower()
        ):
            app.logger.warning(
                "WARNING: Using SQLite database in production is not recommended. Set DATABASE_URL to a robust database like PostgreSQL."
            )
        if not Config.GEMINI_API_KEY and not Config.USE_LOCAL:
            # Warning instead of error, maybe deployment allows local only
            app.logger.warning(
                "WARNING: GEMINI_API_KEY is not set, and USE_LOCAL is false. AI fallback might not be available."
            )
        app.logger.info("Production configuration loaded.")


# Dictionary to easily access configuration classes by name
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
