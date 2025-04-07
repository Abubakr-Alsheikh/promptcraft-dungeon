import logging
from typing import Tuple
from flask import Blueprint, request, jsonify, current_app
from pydantic import ValidationError

# TODO: Implement proper Dependency Injection (e.g., Flask-Injector or App Context Factory)
# For now, instantiate services per request - acceptable for simple cases but not ideal.
from ..services.game_service import GameService
from ..services.ai_service import AIService
from ..schemas.game import (
    StartGameRequest,
    CommandRequest,
    InitialStateResponse,
    CommandResponse,
    GetStateResponse,
    ErrorResponse,
)
from ..extensions import limiter, db
from ..models.game import GameState  # Keep GameState for type hinting if needed

logger = logging.getLogger(__name__)
game_bp = Blueprint("game", __name__, url_prefix="/api/game")  # Add prefix for clarity

# --- Helper Functions (Consider moving to a utils or factory module later) ---


def get_services() -> Tuple[AIService, GameService]:
    """Instantiates and returns AI and Game services."""
    # WARNING: This creates new instances per request. See TODO above.
    ai_service = AIService()
    game_service = GameService(ai_service=ai_service)
    return ai_service, game_service


# --- Routes ---


@game_bp.route("/start", methods=["POST"])
@limiter.limit(lambda: current_app.config.get("RATE_LIMIT", "5 per minute"))
def start_game():
    """Starts a new game session."""
    ai_service, game_service = get_services()
    try:
        request_data = StartGameRequest.model_validate(request.get_json())
        logger.info(
            f"Received start game request: Player='{request_data.playerName}', Difficulty='{request_data.difficulty}'"
        )

        # Call service to start the game
        game_state, error = game_service.start_new_game(
            player_name=request_data.playerName or "Adventurer",
            difficulty=request_data.difficulty or "medium",
        )

        if error or not game_state:
            logger.error(f"Failed to start game: {error}")
            err_resp = ErrorResponse(
                error="Game Start Failed",
                message=error or "Unknown error during game creation.",
            )
            return (
                jsonify(err_resp.model_dump()),
                500,
            )  # Internal error if game can't start

        # Map the initial game state to the frontend response structure
        frontend_state_data = game_service.get_game_state_for_frontend(game_state)
        if not frontend_state_data:
            logger.error(
                f"Failed to map initial game state {game_state.id} for frontend."
            )
            err_resp = ErrorResponse(
                error="Internal Server Error",
                message="Failed to prepare initial game state view.",
            )
            return jsonify(err_resp.model_dump()), 500

        # Construct the successful response, including the game ID
        response_data = {
            **frontend_state_data,
            "game_id": game_state.id,
            # Initial message can be generic or based on first room title/desc
            "message": f"Welcome, {game_state.player.name}! Your adventure begins in {frontend_state_data.get('roomTitle', 'a mysterious place')}...",
            # No specific sound effect needed for start usually, unless AI suggests one
            "soundEffect": None,  # Or potentially from initial AI response if it provided one
        }

        # Validate the final response structure against the Pydantic schema
        validated_response = InitialStateResponse.model_validate(response_data)

        logger.info(
            f"Game {game_state.id} started successfully for player '{game_state.player.name}'."
        )
        return jsonify(validated_response.model_dump()), 200  # OK

    except ValidationError as e:
        logger.warning(f"Start game request validation failed: {e.errors()}")
        err_resp = ErrorResponse(error="Invalid Request Data", details=e.errors())
        return jsonify(err_resp.model_dump()), 400  # Bad Request
    except Exception as e:
        logger.exception("Unexpected error in /start endpoint.")
        err_resp = ErrorResponse(
            error="Internal Server Error",
            message=f"An unexpected error occurred: {str(e)}",
        )
        return jsonify(err_resp.model_dump()), 500


@game_bp.route("/command", methods=["POST"])
@limiter.limit(
    lambda: current_app.config.get("RATE_LIMIT", "10 per minute")
)  # Allow slightly more commands
def handle_command():
    """Handles a player command within a game session."""
    ai_service, game_service = get_services()
    try:
        request_data = CommandRequest.model_validate(request.get_json())
        game_id = request_data.game_id
        command = request_data.command
        logger.info(f"Received command '{command}' for game ID {game_id}")

        # Call service to handle the command
        # It returns updated state (or original on error), the AI response object, and any error message
        updated_state, ai_response, error = game_service.handle_player_command(
            game_state_id=game_id, command=command
        )

        # Handle errors returned from the service
        if error or not updated_state:
            logger.error(f"Error processing command for game {game_id}: {error}")
            status_code = 404 if "not found" in (error or "").lower() else 500
            # Simple error response, don't try to return partial state
            err_resp = ErrorResponse(
                error="Command Failed", message=error or "Failed to process command."
            )
            return jsonify(err_resp.model_dump()), status_code

        # --- Command processed successfully ---
        if not ai_response:  # Should not happen if error is None, but check defensively
            logger.error(
                f"Command processed for game {game_id} but AI response object was missing."
            )
            err_resp = ErrorResponse(
                error="Internal Server Error",
                message="Command processed but failed to get AI details.",
            )
            return jsonify(err_resp.model_dump()), 500

        # Map the successfully updated game state for the frontend
        frontend_state_data = game_service.get_game_state_for_frontend(updated_state)
        if not frontend_state_data:
            logger.error(
                f"Failed to map updated game state {updated_state.id} for frontend after successful command."
            )
            # This indicates an internal mapping issue
            err_resp = ErrorResponse(
                error="Internal Server Error",
                message="Failed to prepare updated game state view.",
            )
            return jsonify(err_resp.model_dump()), 500

        # Construct the successful response
        response_data = {
            "success": True,
            "message": ai_response.action_result_description,  # Use AI's immediate action feedback
            "description": frontend_state_data[
                "description"
            ],  # Persistent room description from mapped state
            "playerStats": frontend_state_data["playerStats"],
            "updatedInventory": frontend_state_data[
                "inventory"
            ],  # Use 'inventory' key from mapped state
            "roomTitle": frontend_state_data["roomTitle"],
            "soundEffect": ai_response.sound_effect,  # Sound effect suggested by AI
            "game_id": updated_state.id,
            # Include other state parts if CommandResponse schema requires them
            "difficulty": frontend_state_data.get("difficulty"),
            "roomsCleared": frontend_state_data.get("roomsCleared"),
        }

        # Validate the final response structure
        validated_response = CommandResponse.model_validate(response_data)

        logger.info(f"Command '{command}' processed successfully for game {game_id}.")
        return jsonify(validated_response.model_dump()), 200  # OK

    except ValidationError as e:
        logger.warning(f"/command request validation failed: {e.errors()}")
        err_resp = ErrorResponse(error="Invalid Request Data", details=e.errors())
        return jsonify(err_resp.model_dump()), 400  # Bad Request
    except Exception as e:
        logger.exception(f"Unexpected error in /command endpoint for game.")
        err_resp = ErrorResponse(
            error="Internal Server Error",
            message=f"An unexpected error occurred: {str(e)}",
        )
        return jsonify(err_resp.model_dump()), 500


@game_bp.route("/state/<int:game_id>", methods=["GET"])
@limiter.limit("10 per minute")
def get_game_state(game_id: int):
    """Retrieves the current state of a game session."""
    ai_service, game_service = get_services()  # GameService needed for mapping
    logger.info(f"Request received for game state ID: {game_id}")
    try:
        # Load game state - could potentially load less data if only specific parts needed
        # Using eager loading here ensures player/inventory are available for mapping
        game_state = db.session.get(
            GameState,
            game_id,
            options=[
                selectinload(GameState.player)
                .selectinload(Player.inventory_items)
                .joinedload(PlayerInventoryItem.item)
                # No need to load chat_messages for GET state usually
            ],
        )

        if not game_state or not game_state.player:
            logger.warning(f"Game state {game_id} not found for GET request.")
            err_resp = ErrorResponse(
                error="Not Found", message="Game session not found."
            )
            return jsonify(err_resp.model_dump()), 404  # Not Found

        # Map the current state to the frontend structure
        frontend_state_data = game_service.get_game_state_for_frontend(game_state)
        if not frontend_state_data:
            logger.error(
                f"Failed to map existing game state {game_id} for GET request."
            )
            err_resp = ErrorResponse(
                error="Internal Server Error",
                message="Failed to retrieve full game state details.",
            )
            return jsonify(err_resp.model_dump()), 500

        # Construct the successful response
        response_data = {
            **frontend_state_data,
            "game_id": game_state.id,
            "message": "Current game state retrieved successfully.",
            "soundEffect": None,
        }

        # Validate using the specific GetStateResponse schema
        validated_response = GetStateResponse.model_validate(response_data)

        logger.debug(f"Successfully retrieved state for game {game_id}.")
        return jsonify(validated_response.model_dump()), 200  # OK

    except Exception as e:
        logger.exception(f"Unexpected error in /state/{game_id} endpoint.")
        err_resp = ErrorResponse(
            error="Internal Server Error",
            message=f"An unexpected error occurred: {str(e)}",
        )
        return jsonify(err_resp.model_dump()), 500
