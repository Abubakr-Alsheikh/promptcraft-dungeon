# backend/app/routes/game_routes.py
import logging

# import json # Not needed directly here now
from flask import Blueprint, request, jsonify, current_app
from typing import Optional
from pydantic import ValidationError

from ..services.game_service import GameService
from ..services.ai_service import AIService
from ..schemas.game import (
    StartGameRequest,
    CommandRequest,
    InitialStateResponse,  # Expects description, playerStats, inventory, roomTitle
    CommandResponse,  # Expects message, description, playerStats, updatedInventory, roomTitle, etc.
    GetStateResponse,  # Expects description, playerStats, inventory, roomTitle
)
from ..extensions import limiter, db
from ..models.game import GameState

# from ..models.ai_responses import AIResponse # Not needed directly here now

logger = logging.getLogger(__name__)
game_bp = Blueprint("game", __name__)


# --- Dependency Injection (simplified) ---
# Consider using Flask-Injector or similar for more robust DI
def get_ai_service():
    # In a real app, manage service instances better (e.g., singleton within request context)
    return AIService()


def get_game_service():
    return GameService(ai_service=get_ai_service())


# --- Routes ---


@game_bp.route("/start", methods=["POST"])
@limiter.limit(lambda: current_app.config["RATE_LIMIT"])
def start_game():
    game_service = get_game_service()
    try:
        request_data = StartGameRequest.model_validate(request.get_json())
        logger.info(f"Received start game request: {request_data.model_dump()}")

        game_state, error = game_service.start_new_game(
            player_name=request_data.playerName or "Adventurer",
            difficulty=request_data.difficulty or "medium",
        )

        if error or not game_state:
            logger.error(f"Failed to start game: {error}")
            return (
                jsonify(
                    {
                        "error": "Failed to start game",
                        "message": error or "Unknown error",
                    }
                ),
                500,
            )

        # Map the initial backend GameState to the frontend's expected schema
        # This now includes the initial room description and title
        frontend_state = game_service.get_game_state_for_frontend(game_state)

        if not frontend_state:  # Handle error case from mapping function
            logger.error(
                f"Failed to map initial game state {game_state.id} for frontend."
            )
            return (
                jsonify(
                    {
                        "error": "Internal server error",
                        "message": "Failed to prepare game state.",
                    }
                ),
                500,
            )

        # Construct the response data including the crucial game_id
        response_data = {
            **frontend_state,  # Includes playerStats, inventory, description, roomTitle
            "game_id": game_state.id,
            "message": "Welcome, your adventure begins!",  # Generic welcome message for start
        }

        # Validate response against schema before sending
        validated_response = InitialStateResponse.model_validate(response_data)

        logger.info(f"Game {game_state.id} started successfully.")
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
        request_data = CommandRequest.model_validate(json_data)
        game_id = request_data.game_id
        command = request_data.command

        logger.info(f"Received command '{command}' for game ID {game_id}")

        # handle_player_command now returns the updated state AND the AI response object
        updated_state, ai_response, error = game_service.handle_player_command(
            game_state_id=game_id, command=command
        )

        # Handle errors during command processing
        if error or not updated_state:  # If state is None, a major error occurred
            logger.error(f"Error processing command for game {game_id}: {error}")
            status_code = 404 if "not found" in (error or "").lower() else 500
            # Try to get last known state data *if* updated_state exists but AI failed later
            last_known_state_data = {}
            error_description = "State unclear due to error."
            if updated_state:  # Only map if state object exists, even if AI part failed
                try:
                    last_known_state_data = game_service.get_game_state_for_frontend(
                        updated_state
                    )
                    error_description = last_known_state_data.get(
                        "description", error_description
                    )
                except Exception as map_err:
                    logger.error(
                        f"Error mapping state during error handling: {map_err}"
                    )

            # Construct error response matching CommandResponse structure where possible
            return (
                jsonify(
                    {
                        "success": False,
                        "message": error
                        or "Command processing failed or AI did not respond.",  # The error message from service
                        "description": error_description,  # Last known room description if possible
                        "playerStats": last_known_state_data.get(
                            "playerStats"
                        ),  # Last known stats
                        "updatedInventory": last_known_state_data.get(
                            "inventory"
                        ),  # Last known inventory
                        "roomTitle": last_known_state_data.get("roomTitle"),
                        "soundEffect": None,
                        "game_id": game_id,
                    }
                ),
                status_code,
            )

        # Command processed successfully, AI responded
        # Map the successfully updated backend state to the frontend schema
        frontend_state = game_service.get_game_state_for_frontend(updated_state)

        if not frontend_state:  # Handle mapping error even on success path
            logger.error(
                f"Failed to map updated game state {updated_state.id} for frontend after successful command."
            )
            # This indicates an internal issue, likely in the mapping functions
            return (
                jsonify(
                    {
                        "error": "Internal server error",
                        "message": "Failed to prepare updated game state.",
                    }
                ),
                500,
            )

        # Construct the successful response matching CommandResponse schema
        response_data = {
            "success": True,
            # Key Change: Use AI's action_result_description for the immediate message
            "message": ai_response.action_result_description,
            # Key Change: Use the persistent description from the mapped state
            "description": frontend_state["description"],
            "playerStats": frontend_state["playerStats"],
            "updatedInventory": frontend_state["inventory"],
            "roomTitle": frontend_state["roomTitle"],  # Include updated room title
            "soundEffect": ai_response.sound_effect,
            "game_id": updated_state.id,
        }

        # Validate the final response structure
        validated_response = CommandResponse.model_validate(response_data)

        logger.info(f"Command '{command}' processed successfully for game {game_id}.")
        return jsonify(validated_response.model_dump()), 200

    except ValidationError as e:
        logger.warning(f"Command request validation failed: {e.errors()}")
        return jsonify({"error": "Invalid request data", "details": e.errors()}), 400
    except Exception as e:
        logger.exception(f"Unexpected error in /command endpoint.")
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


@game_bp.route("/state/<int:game_id>", methods=["GET"])
@limiter.limit("10 per minute")  # Consider adjusting rate limit
def get_game_state(game_id: int):
    game_service = get_game_service()  # Get service instance
    logger.info(f"Request received for game state ID: {game_id}")
    try:
        game_state: Optional[GameState] = db.session.get(GameState, game_id)
        if not game_state or not game_state.player:
            logger.warning(f"Game state {game_id} not found for GET request.")
            return (
                jsonify({"error": "Not Found", "message": "Game session not found."}),
                404,
            )

        # Map the current state to the frontend schema
        frontend_state = game_service.get_game_state_for_frontend(game_state)

        if not frontend_state:  # Handle mapping error
            logger.error(
                f"Failed to map existing game state {game_id} for GET request."
            )
            return (
                jsonify(
                    {
                        "error": "Internal server error",
                        "message": "Failed to retrieve game state details.",
                    }
                ),
                500,
            )

        response_data = {
            **frontend_state,  # Includes playerStats, inventory, description, roomTitle
            "game_id": game_state.id,
            "message": "Current game state retrieved.",
        }

        # Validate using the specific GetStateResponse schema
        validated_response = GetStateResponse.model_validate(response_data)

        return jsonify(validated_response.model_dump()), 200

    except Exception as e:
        logger.exception(f"Unexpected error in /state/{game_id} endpoint.")
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
