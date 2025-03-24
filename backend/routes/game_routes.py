from flask import Blueprint, request, jsonify
from services.game_service import GameService
from services.ai_service import AIService
from validators import validate_game_action
from models import GameState, Player

game_bp = Blueprint("game", __name__)


@game_bp.route("/start", methods=["POST"])
def start_game():
    try:
        player_name = request.json.get("playerName", "Adventurer")
        difficulty = request.json.get("difficulty", "medium")

        # Initialize game state
        player = Player(name=player_name)
        game_state = GameState(player=player, difficulty=difficulty)

        # Generate initial room
        response = AIService.generate_initial_room(game_state)

        return jsonify({"game_state": game_state.to_dict(), "room": response})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@game_bp.route("/action", methods=["POST"])
@validate_game_action
def handle_action():
    try:
        game_data = request.get_json()
        action = game_data["action"]
        game_state = GameState.from_dict(game_data["game_state"])

        # Process action and update game state
        updated_state = GameService.process_action(game_state, action)

        # Generate AI response
        ai_response = AIService.generate_response(updated_state, action)

        return jsonify({"game_state": updated_state.to_dict(), "result": ai_response})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
