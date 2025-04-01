# backend/app/routes/game_routes.py
import logging
import json
from flask import Blueprint, request, jsonify, current_app
from typing import Optional
from pydantic import ValidationError

from ..services.game_service import GameService
from ..services.ai_service import AIService
from ..schemas.game import (
    StartGameRequest,
    CommandRequest,
    InitialStateResponse,  # Updated Response Schema
    CommandResponse,  # Updated Response Schema
    GetStateResponse,  # Schema for GET /state
)
from ..extensions import limiter, db
from ..models.game import GameState

logger = logging.getLogger(__name__)
game_bp = Blueprint("game", __name__)


# --- Dependency Injection (simplified) ---
def get_ai_service():
    return AIService()


def get_game_service():
    return GameService(ai_service=get_ai_service())


# --- Routes ---


@game_bp.route("/start", methods=["POST"])
@limiter.limit(lambda: current_app.config["RATE_LIMIT"])
def start_game():
    game_service = get_game_service()
    try:
        # Validate request body using Pydantic
        request_data = StartGameRequest.model_validate(request.get_json())
        logger.info(f"Received start game request: {request_data.model_dump()}")

        game_state, error = game_service.start_new_game(
            player_name=request_data.playerName or "Adventurer",  # Use default if None
            difficulty=request_data.difficulty or "medium",  # Use default if None
        )

        if error or not game_state:
            logger.error(f"Failed to start game: {error}")
            return jsonify({"error": "Failed to start game", "message": error}), 500

        # Map the initial backend GameState to the frontend's expected schema
        frontend_state = game_service.get_game_state_for_frontend(game_state)

        # Construct the response data including the crucial game_id
        response_data = {
            **frontend_state,
            "game_id": game_state.id,  # Include the game_id
            "message": "New game started successfully!",
        }

        # Validate response against schema before sending
        validated_response = InitialStateResponse.model_validate(response_data)

        return jsonify(validated_response.model_dump()), 200

    except ValidationError as e:
        logger.warning(f"Start game request validation failed: {e.errors()}")
        return jsonify({"error": "Invalid request data", "details": e.errors()}), 400
    except Exception as e:
        logger.exception("Unexpected error in /start endpoint.")
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


@game_bp.route("/command", methods=["POST"])
@limiter.limit(lambda: current_app.config["RATE_LIMIT"])
def handle_command():
    game_service = get_game_service()
    try:
        json_data = request.get_json()
        # Validate the entire command data using the updated schema
        request_data = CommandRequest.model_validate(json_data)
        game_id = request_data.game_id  # Get game_id from validated data
        command = request_data.command

        logger.info(f"Received command '{command}' for game ID {game_id}")

        updated_state, ai_response, error = game_service.handle_player_command(
            game_state_id=game_id, command=command
        )

        if error or not updated_state or not ai_response:
            logger.error(f"Error processing command for game {game_id}: {error}")
            status_code = 404 if "not found" in (error or "").lower() else 500
            last_known_state_data = {}
            if updated_state:  # Try to map even if AI failed after load
                try:
                    last_known_state_data = game_service.get_game_state_for_frontend(
                        updated_state
                    )
                except Exception as map_err:
                    logger.error(
                        f"Error mapping state during error handling: {map_err}"
                    )

            return (
                jsonify(
                    {
                        "error": "Command processing failed",
                        "message": error or "AI failed to respond or internal error.",
                        # Attempt to send last known state details if possible
                        "playerStats": last_known_state_data.get("playerStats"),
                        "inventory": last_known_state_data.get("inventory"),
                        "description": last_known_state_data.get(
                            "description", "State unclear."
                        ),
                        "game_id": game_id,  # Return the game_id even on error
                        "success": False,
                    }
                ),
                status_code,
            )

        # Map the updated backend state to the frontend schema
        frontend_state = game_service.get_game_state_for_frontend(updated_state)

        # Construct the response matching CommandResponse schema
        response_data = {
            "success": True,
            "message": ai_response.action_result_description,
            "description": frontend_state["description"],
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


@game_bp.route("/state/<int:game_id>", methods=["GET"])
@limiter.limit("10 per minute")
def get_game_state(game_id: int):
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

        frontend_state = game_service.get_game_state_for_frontend(game_state)
        response_data = {
            **frontend_state,
            "game_id": game_state.id,
            "message": "Current game state retrieved.",
        }

        # Validate using the specific GetStateResponse schema
        validated_response = GetStateResponse.model_validate(response_data)

        return jsonify(validated_response.model_dump()), 200

    except Exception as e:
        logger.exception(f"Unexpected error in /state/{game_id} endpoint.")
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
