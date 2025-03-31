# backend/app/routes/game_routes.py
import logging
import json  # Import json
from flask import Blueprint, request, jsonify, current_app
from typing import Optional
from pydantic import ValidationError

from ..services.game_service import GameService
from ..services.ai_service import AIService
from ..schemas.game import (
    StartGameRequest,
    CommandRequest,
    InitialStateResponse,
    CommandResponse,
    GameStateSchema,
)
from ..extensions import limiter, db  # Import db
from ..models.game import GameState  # Import GameState model

logger = logging.getLogger(__name__)
game_bp = Blueprint("game", __name__)


# --- Dependency Injection (simplified) ---
# In a larger app, consider Flask-Injector or similar, but manual is fine here.
def get_ai_service():
    # Cache instance on app context? For now, create per request or reuse if stateless
    return AIService()


def get_game_service():
    # Create GameService with the AI service instance
    return GameService(ai_service=get_ai_service())


# --- Routes ---


# This endpoint now aligns with frontend's getInitialState expectation (conceptually)
# If you want true persistence, this might load based on session/user ID
@game_bp.route("/start", methods=["POST"])
@limiter.limit(lambda: current_app.config["RATE_LIMIT"])  # Apply specific rate limit
def start_game():
    """
    Starts a *new* game session.
    Frontend equivalent: Kicking off a new adventure.
    """
    game_service = get_game_service()
    try:
        # Validate request body using Pydantic
        request_data = StartGameRequest.model_validate(request.get_json())
        logger.info(f"Received start game request: {request_data.model_dump()}")

        game_state, error = game_service.start_new_game(
            player_name=request_data.playerName, difficulty=request_data.difficulty
        )

        if error or not game_state:
            logger.error(f"Failed to start game: {error}")
            return jsonify({"error": "Failed to start game", "message": error}), 500

        # Map the initial backend GameState to the frontend's expected schema
        frontend_state = game_service.get_game_state_for_frontend(game_state)

        # Include the game state ID in the response so frontend can use it for subsequent commands
        response_data = {
            **frontend_state,
            # Add game_id to be stored by frontend for subsequent calls
            "game_id": game_state.id,
            "message": "New game started successfully!",
        }

        # Validate response against schema before sending (good practice)
        validated_response = InitialStateResponse.model_validate(response_data)

        return jsonify(validated_response.model_dump()), 200

    except ValidationError as e:
        logger.warning(f"Start game request validation failed: {e.errors()}")
        return jsonify({"error": "Invalid request data", "details": e.errors()}), 400
    except Exception as e:
        logger.exception("Unexpected error in /start endpoint.")
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


# This endpoint aligns with frontend's sendCommand
@game_bp.route("/command", methods=["POST"])
@limiter.limit(lambda: current_app.config["RATE_LIMIT"])
def handle_command():
    """
    Handles a player command for an ongoing game session.
    Frontend equivalent: Sending any player input ('look', 'attack', 'go north').
    """
    game_service = get_game_service()
    try:
        json_data = request.get_json()
        # We need the game_id from the frontend now to load the correct state
        game_id = json_data.get("game_id")
        if not game_id:
            return jsonify({"error": "Missing 'game_id' in request"}), 400

        # Validate the rest of the command data
        request_data = CommandRequest.model_validate(json_data)
        logger.info(f"Received command '{request_data.command}' for game ID {game_id}")

        # Process the command using the service
        updated_state, ai_response, error = game_service.handle_player_command(
            game_state_id=game_id, command=request_data.command
        )

        # Handle cases where the game state couldn't be processed or AI failed
        if error or not updated_state or not ai_response:
            logger.error(f"Error processing command for game {game_id}: {error}")
            # Still return *some* state if possible, even on error, maybe the state before the command?
            # If updated_state exists, use it, otherwise load original? Needs careful thought.
            # For now, return error clearly.
            status_code = 404 if "not found" in (error or "").lower() else 500
            # Try to return the last known state if available
            last_known_state_data = {}
            if (
                updated_state
            ):  # If state exists even with error (e.g. AI fail after load)
                last_known_state_data = game_service.get_game_state_for_frontend(
                    updated_state
                )

            return (
                jsonify(
                    {
                        "error": "Command processing failed",
                        "message": error or "AI failed to respond or internal error.",
                        **last_known_state_data,  # Send last known state if possible
                    }
                ),
                status_code,
            )

        # Map the updated backend state to the frontend schema
        frontend_state = game_service.get_game_state_for_frontend(updated_state)

        # Construct the response matching CommandResponse schema
        response_data = {
            "success": True,  # Assume success if no error occurred
            # Use the primary narrative from AI response
            "message": ai_response.action_result_description,
            # The description might be the same as message, or a more detailed room view
            "description": frontend_state[
                "description"
            ],  # Get description from mapped state
            "playerStats": frontend_state["playerStats"],
            "updatedInventory": frontend_state["inventory"],
            "soundEffect": ai_response.sound_effect,
            "game_id": updated_state.id,  # Return game_id again
        }

        # Validate the final response structure
        validated_response = CommandResponse.model_validate(response_data)

        return jsonify(validated_response.model_dump()), 200

    except ValidationError as e:
        logger.warning(f"Command request validation failed: {e.errors()}")
        return jsonify({"error": "Invalid request data", "details": e.errors()}), 400
    except Exception as e:
        logger.exception(f"Unexpected error in /command endpoint.")
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


# Optional: Add an endpoint to explicitly load state if needed
@game_bp.route("/state/<int:game_id>", methods=["GET"])
@limiter.limit("10 per minute")  # Less frequent access potentially
def get_game_state(game_id: int):
    """Gets the current state of a specific game session."""
    game_service = get_game_service()
    logger.info(f"Request received for game state ID: {game_id}")
    try:
        game_state: Optional[GameState] = db.session.get(GameState, game_id)
        if not game_state or not game_state.player:
            logger.warning(f"Game state {game_id} not found for GET request.")
            return (
                jsonify({"error": "Not Found", "message": "Game session not found."}),
                404,
            )

        # Map to frontend schema
        frontend_state = game_service.get_game_state_for_frontend(game_state)
        response_data = {**frontend_state, "game_id": game_state.id}

        # Validate (using GameStateSchema as base for required fields)
        validated_response = GameStateSchema.model_validate(
            frontend_state
        )  # Use the base schema

        return jsonify(validated_response.model_dump()), 200

    except Exception as e:
        logger.exception(f"Unexpected error in /state/{game_id} endpoint.")
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
