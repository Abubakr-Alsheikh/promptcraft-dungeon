import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "a_very_secret_key_for_dev")
    DEBUG = False
    TESTING = False

    # Rate Limiting
    RATE_LIMIT = os.environ.get("RATE_LIMIT", "5 per minute")
    DEFAULT_RATE_LIMITS = ["200 per day", "50 per hour"]

    # CORS
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")

    # AI Service Config
    OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    USE_LOCAL = os.environ.get("USE_LOCAL", "false").lower() == "true"
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "deepseek-r1:1.5B")
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    AI_REQUEST_TIMEOUT = int(
        os.environ.get("AI_REQUEST_TIMEOUT", 60)
    )  # Timeout for AI calls

    # Logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

    # Database (Using SQLite by default for easy setup)
    # For PostgreSQL: postgresql://user:password@host:port/database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or "sqlite:///" + os.path.join(
        basedir, "..", "instance", "app.db"
    )  # Store DB in instance folder
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def init_app(app):
        # Create instance folder if it doesn't exist
        instance_path = os.path.join(basedir, "..", "instance")
        if not os.path.exists(instance_path):
            os.makedirs(instance_path)
        app.logger.info(f"Instance path: {instance_path}")


class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    # Relax rate limits for development if needed
    # DEFAULT_RATE_LIMITS = ["100 per minute"]


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # Use in-memory DB for tests
    WTF_CSRF_ENABLED = False  # Disable CSRF forms validation in tests


class ProductionConfig(Config):
    # Ensure critical production settings are enforced
    if not Config.SECRET_KEY or Config.SECRET_KEY == "a_very_secret_key_for_dev":
        raise ValueError("Production SECRET_KEY must be set to a strong value")
    if not Config.GEMINI_API_KEY and not Config.USE_LOCAL:
        raise ValueError(
            "GEMINI_API_KEY must be set in production if not using only local LLM"
        )
    if not os.environ.get("DATABASE_URL"):
        # Strongly recommend using PostgreSQL or similar for production
        print("WARNING: Using default SQLite database in production. Set DATABASE_URL.")
    # Add any other production-specific settings (e.g., logging formatters)


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
