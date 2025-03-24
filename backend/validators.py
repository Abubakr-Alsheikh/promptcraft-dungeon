from functools import wraps
from flask import request, jsonify


def validate_game_action(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        if "action" not in data or "game_state" not in data:
            return jsonify({"error": "Missing required fields"}), 400
        return f(*args, **kwargs)

    return wrapper
