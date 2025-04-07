import os
import sys
import logging  # Import logging
from dotenv import load_dotenv

# Add the project root directory to the Python path if running script directly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables from .env file *before* app creation
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(dotenv_path):
    print(f"Loading environment variables from: {dotenv_path}")
    load_dotenv(dotenv_path)
else:
    print("Note: .env file not found, using system environment variables or defaults.")

# Import create_app factory function from the app package
from app import create_app

# REMOVE: from app.extensions import configure_logging # No longer needed here

# Get a logger instance for this script
log = logging.getLogger(__name__)  # Use logger named '__main__'

# Determine configuration type
config_name = os.getenv("FLASK_CONFIG", "development")
print(f"Using configuration: '{config_name}'")

# Create the Flask app instance using the factory
app = create_app(config_name)

if __name__ == "__main__":
    host = os.environ.get("FLASK_RUN_HOST", "127.0.0.1")
    try:
        port = int(os.environ.get("PORT", 5001))
    except ValueError:
        # Use app.logger if app exists, otherwise fallback print/log
        app.logger.warning("Invalid PORT environment variable. Using default 5001.")
        port = 5001

    use_debugger = app.debug
    use_reloader = app.debug

    # Use the logger obtained earlier (named '__main__')
    log.info(
        f"Starting server on {host}:{port} (Debug: {use_debugger}, Reloader: {use_reloader})"
    )
    app.run(host=host, port=port, debug=use_debugger, use_reloader=use_reloader)
