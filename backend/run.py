import os
from dotenv import load_dotenv

# Load environment variables from .env file BEFORE importing the app
# Useful for development environment
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

from app import create_app

# Use environment variable for configuration or default to DevelopmentConfig
config_name = os.getenv("FLASK_CONFIG", "development")
app = create_app(config_name)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    # Use debug=True only in development, controlled by config
    app.run(port=port, debug=app.config.get("DEBUG", True))
