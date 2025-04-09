import os
import sys
from dotenv import load_dotenv

# Add the project root directory to the Python path if running script directly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables from .env file *before* app creation
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(dotenv_path):
    print(f"run.py: Loading environment variables from: {dotenv_path}")
    load_dotenv(dotenv_path)
else:
    print("run.py: .env file not found, using system environment variables or defaults")

# Import create_app factory function from the app package
from app import create_app

if __name__ == "__main__":
    # Determine configuration type - defaults to 'development' for run.py
    config_name = os.getenv("FLASK_CONFIG", "development")
    print(f"run.py: Using configuration: '{config_name}'")

    # Create the Flask app instance *inside* the main block
    app = create_app(config_name)

    # Use app.logger *after* the app is created and logging is configured
    host = os.environ.get("FLASK_RUN_HOST", "127.0.0.1")
    try:
        port = int(os.environ.get("PORT", 5001))
    except ValueError:
        app.logger.warning("Invalid PORT environment variable. Using default 5001.")
        port = 5001

    use_debugger = app.debug
    use_reloader = app.debug  # Usually True in development

    app.logger.info(
        f"Starting Flask development server on http://{host}:{port} "
        f"(Debug: {use_debugger}, Reloader: {use_reloader})"
    )
    # Run using Flask's development server
    app.run(host=host, port=port, debug=use_debugger, use_reloader=use_reloader)
