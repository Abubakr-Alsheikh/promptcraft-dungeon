import os
import sys
import logging
from dotenv import load_dotenv

# --- Path Setup ---
# Add the project root directory (backend/) to the Python path
# This ensures that 'app' can be imported correctly
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Environment Loading ---
# Load environment variables from .env file if it exists
# Crucial for Gunicorn to pick up production settings
dotenv_path = os.path.join(project_root, ".env")
if os.path.exists(dotenv_path):
    print(f"WSGI: Loading environment variables from: {dotenv_path}")
    load_dotenv(dotenv_path)
else:
    print("WSGI: Note: .env file not found, relying on system environment variables.")

# --- App Creation ---
# Import the application factory
from app import create_app

# Determine configuration type - *MUST* default to 'production' for WSGI
# Gunicorn should be launched with FLASK_CONFIG=production set in the environment
config_name = os.getenv("FLASK_CONFIG", "production")
print(f"WSGI: Using configuration: '{config_name}'")

# Create the Flask app instance using the factory
# Gunicorn will look for this 'app' variable by default (wsgi:app)
app = create_app(config_name)

# --- Optional: Configure Gunicorn Logging ---
# If you want Gunicorn's own logs (access/error) to use your Flask app's
# logging handlers, you can potentially integrate them here.
# This is more advanced and often Gunicorn's default file/stderr logging is sufficient.
# Example (might need adjustment based on your exact logging setup):
if __name__ != "__main__":  # Only when run by a WSGI server like Gunicorn
    gunicorn_logger = logging.getLogger("gunicorn.error")
    # If using dictConfig, Flask's root logger might already be set up
    # You might just need to ensure Gunicorn logs at the right level
    app.logger.handlers.extend(gunicorn_logger.handlers)  # Combine handlers (careful!)
    # Or configure Gunicorn separately using its command-line args (--log-config)
    app.logger.info(
        f"WSGI entry point loaded for config '{config_name}'. Gunicorn logging might be integrated."
    )

# The 'app' variable is now ready for Gunicorn
