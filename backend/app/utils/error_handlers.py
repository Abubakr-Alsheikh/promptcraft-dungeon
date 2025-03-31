import logging
from flask import jsonify
from pydantic import ValidationError

logger = logging.getLogger(__name__)


def register_error_handlers(app):

    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        logger.warning(f"Request validation failed: {e.errors()}")
        return (
            jsonify(
                {
                    "error": "Validation Error",
                    "message": "Invalid data provided in request.",
                    "details": e.errors(),
                }
            ),
            400,
        )

    @app.errorhandler(400)
    def bad_request_error(e):
        logger.warning(f"Bad Request (400): {e.description}")
        return (
            jsonify(
                {
                    "error": "Bad Request",
                    "message": e.description
                    or "The server could not understand the request.",
                }
            ),
            400,
        )

    @app.errorhandler(404)
    def not_found_error(e):
        logger.warning(f"Not Found (404): {e.description}")
        return (
            jsonify(
                {
                    "error": "Not Found",
                    "message": e.description or "The requested resource was not found.",
                }
            ),
            404,
        )

    @app.errorhandler(405)
    def method_not_allowed_error(e):
        logger.warning(f"Method Not Allowed (405): {e.description}")
        return (
            jsonify(
                {
                    "error": "Method Not Allowed",
                    "message": e.description
                    or "The method is not allowed for the requested URL.",
                }
            ),
            405,
        )

    @app.errorhandler(429)
    def ratelimit_handler(e):
        logger.warning(f"Rate Limit Exceeded (429): {e.description}")
        return (
            jsonify(
                {
                    "error": "Rate Limit Exceeded",
                    "message": e.description
                    or "You have exceeded your request rate limit.",
                }
            ),
            429,
        )

    @app.errorhandler(500)
    def internal_server_error(e):
        # Log the original exception if available
        original_exception = getattr(e, "original_exception", None)
        logger.error(f"Internal Server Error (500): {e}", exc_info=original_exception)
        return (
            jsonify(
                {
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred on the server. Please try again later.",
                }
            ),
            500,
        )

    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        # Catch-all for any other unhandled exceptions
        logger.exception(f"Unhandled Exception: {e}")  # Log with stack trace
        return (
            jsonify(
                {
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred.",
                }
            ),
            500,
        )
