import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from ..extensions import db
from ..models.game import GameState, Player
from ..models.ai_responses import AIResponse, AIEvent, AIEventEffect
from ..prompts.game_prompts import BASE_SYSTEM_PROMPT, INITIAL_ROOM_PROMPT_USER
from ..schemas.game import PlayerStatsSchema, ItemSchema  # Import schemas
from ..services.ai_service import AIService

logger = logging.getLogger(__name__)


class GameService:
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service

    def start_new_game(
        self, player_name: str, difficulty: str
    ) -> Tuple[Optional[GameState], Optional[str]]:
        """
        Initializes a new game state, generates the first room via AI, and saves to DB.
        Returns the initial GameState object and an error message if failed.
        """
        logger.info(f"Starting new game for {player_name}, difficulty {difficulty}")
        try:
            # 1. Create Initial Player and GameState
            player = Player(
                name=player_name,
                health=100,
                max_health=100,
                inventory=[],
                level=1,
                gold=10,
            )  # Start with some gold?
            game_state = GameState(
                player=player, difficulty=difficulty, rooms_cleared=0
            )

            # 2. Prepare context for initial room generation
            context = self._build_ai_context(
                game_state, command="start_game"
            )  # Use a dummy command or None

            # 3. Ask AI Service to generate the initial room description/details
            # Note: The initial prompt might need a slightly different structure/goal
            # than the standard action processing prompt.
            initial_room_ai_response: Optional[AIResponse] = (
                self.ai_service.generate_structured_response(
                    system_prompt_template=BASE_SYSTEM_PROMPT,  # Use base system prompt for consistency
                    user_prompt=INITIAL_ROOM_PROMPT_USER,  # Specific user prompt for starting room
                    context=context,
                )
            )

            if not initial_room_ai_response:
                logger.error("AI failed to generate initial room.")
                return None, "Failed to generate the starting area with AI."

            # 4. Store the initial room description in the GameState
            # The initial response might just have a description and maybe minor events.
            # We store the core description. The concept of a "room object" might just be the description string + exits if needed.
            # Let's assume the initial prompt returns the room description in action_result_description for simplicity here.
            initial_description = initial_room_ai_response.action_result_description
            game_state.current_room_json = json.dumps(
                {  # Store initial room info as JSON
                    "title": "Beginning",  # Or get from AI if it provides title
                    "description": initial_description,
                    "exits": [],  # Or get from AI if provided
                    "events": [
                        event.model_dump()
                        for event in initial_room_ai_response.triggered_events
                    ],  # Store initial events
                }
            )
            logger.debug(f"Initial room generated: {initial_description[:100]}...")

            # 5. Save initial state to Database
            db.session.add(game_state)
            db.session.commit()
            logger.info(f"New game state (ID: {game_state.id}) created and saved.")

            return game_state, None  # Return the created game state, no error

        except Exception as e:
            db.session.rollback()  # Rollback DB changes on error
            logger.exception(f"Error starting new game: {e}")
            return None, f"An unexpected server error occurred: {e}"

    def handle_player_command(
        self, game_state_id: int, command: str
    ) -> Tuple[Optional[GameState], Optional[AIResponse], Optional[str]]:
        """
        Loads game state, sends command+context to AI, applies results, saves state.
        Returns (updated_game_state, ai_response_object, error_message)
        """
        logger.info(f"Handling command '{command}' for game state ID {game_state_id}")
        try:
            # 1. Load Game State from DB
            game_state: Optional[GameState] = db.session.get(GameState, game_state_id)
            if not game_state or not game_state.player:
                logger.error(
                    f"Game state with ID {game_state_id} not found or has no player."
                )
                return None, None, "Game session not found. Please start a new game."

            # 2. Prepare Context for AI
            context = self._build_ai_context(game_state, command)
            logger.debug(f"AI Context: {context}")

            # 3. Get AI Response
            ai_response: Optional[AIResponse] = (
                self.ai_service.generate_structured_response(
                    system_prompt_template=BASE_SYSTEM_PROMPT,
                    user_prompt="{player_command}",  # User prompt is just the command itself here
                    context=context,
                )
            )

            if not ai_response:
                logger.error(f"AI failed to generate response for command: {command}")
                # Return current state without changes, but indicate AI failure
                return (
                    game_state,
                    None,
                    "The Narrator seems lost in thought... (AI failed to respond)",
                )

            logger.debug(
                f"AI Response received: {ai_response.model_dump_json(indent=2)}"
            )

            # 4. Apply AI-dictated changes to Game State
            # Important: Apply effects BEFORE updating the room description
            # in case effects change stats relevant to the description itself.
            self._apply_ai_effects(game_state.player, ai_response)

            # 5. Update room description / Handle potential room change
            current_room_data = game_state.current_room or {}  # Get current room dict
            if ai_response.new_room_description:
                # AI indicates a move to a new room/area
                logger.info(
                    f"Moving to new room described by AI for game {game_state_id}"
                )
                # We might need a new title or the AI could provide one in events/description
                current_room_data["description"] = ai_response.new_room_description
                # Reset events? Or does the AI response include events for the new room? Assume events are action-specific for now.
                # The AI prompt should be clear about whether it generates the *entire* new room state or just the description.
                # For simplicity, let's just update the description. Exits might need explicit asking ("look around").
                current_room_data["title"] = "New Area"  # Placeholder
                current_room_data["exits"] = (
                    []
                )  # Reset exits? Needs clarification in prompt design.
                current_room_data["events"] = []  # Clear old room events?
                game_state.rooms_cleared += (
                    1  # Increment if move is considered clearing
                )
            else:
                # Update description within the *current* room based on action result
                # Append or replace? Let's assume the AI gives the *new* description of the current situation.
                current_room_data["description"] = ai_response.action_result_description
                # We might also want to store the action-specific events here
                current_room_data["events"] = [
                    event.model_dump() for event in ai_response.triggered_events
                ]

            game_state.current_room = current_room_data  # Update the GameState object property (triggers setter)

            # 6. Save Updated State to DB
            db.session.commit()
            logger.info(
                f"Game state {game_state_id} updated and saved after command '{command}'."
            )

            return (
                game_state,
                ai_response,
                None,
            )  # Return updated state, AI response, no error

        except Exception as e:
            db.session.rollback()
            logger.exception(
                f"Error handling command '{command}' for game state {game_state_id}: {e}"
            )
            return None, None, f"An unexpected server error occurred: {e}"

    def _build_ai_context(self, game_state: GameState, command: str) -> Dict[str, Any]:
        """Helper to create the context dictionary for AI prompts."""
        player = game_state.player
        room = game_state.current_room or {
            "description": "An empty void",
            "exits": [],
        }  # Default if no room set

        # Format inventory for the prompt (e.g., "Health Potion (2), Rusty Sword (1)")
        inventory_list = []
        for item_dict in player.inventory:
            name = item_dict.get("name", "Unknown Item")
            qty = item_dict.get("quantity", 1)
            inventory_list.append(f"{name} ({qty})")
        inventory_str = ", ".join(inventory_list) if inventory_list else "Empty"

        return {
            "difficulty": game_state.difficulty,
            "player_name": player.name,
            "health": player.health,
            "max_health": player.max_health,
            "level": player.level,
            "inventory": inventory_str,
            "current_room_description": room.get(
                "description", "You are in an featureless location."
            ),
            "current_room_exits": ", ".join(room.get("exits", [])),
            "player_command": command,
            # Add any other relevant state: time of day, active quests, status effects etc.
        }

    def _apply_ai_effects(self, player: Player, ai_response: AIResponse):
        """Applies effects from AI events to the player state."""
        if not player:
            return

        current_inventory = player.inventory  # Get mutable list

        for event in ai_response.triggered_events:
            if event.effects:
                effects = event.effects
                logger.debug(
                    f"Applying effects from event type '{event.type}': {effects.model_dump()}"
                )

                # Health changes
                if effects.health:
                    try:
                        delta = int(effects.health)
                        player.health = max(
                            0, min(player.max_health, player.health + delta)
                        )
                        logger.info(
                            f"Player health changed by {delta} to {player.health}"
                        )
                    except ValueError:
                        logger.warning(f"Invalid health effect value: {effects.health}")

                # Gold changes
                if effects.gold:
                    try:
                        delta = int(effects.gold)
                        player.gold = max(0, player.gold + delta)
                        logger.info(f"Player gold changed by {delta} to {player.gold}")
                    except ValueError:
                        logger.warning(f"Invalid gold effect value: {effects.gold}")

                # XP changes (add level up logic if needed)
                if effects.xp:
                    try:
                        delta = int(effects.xp)
                        player.experience = max(0, player.experience + delta)
                        logger.info(
                            f"Player XP changed by {delta} to {player.experience}"
                        )
                        # Add level up check here if xp exceeds max for level
                    except ValueError:
                        logger.warning(f"Invalid XP effect value: {effects.xp}")

                # Inventory changes
                # Removals first
                if effects.inventory_remove:
                    items_to_remove = {
                        item_name.lower() for item_name in effects.inventory_remove
                    }
                    new_inventory = []
                    for item_dict in current_inventory:
                        item_name = item_dict.get("name", "").lower()
                        if item_name in items_to_remove:
                            # Simple removal - assumes quantity 1 or remove stack
                            # More complex logic needed for quantity > 1
                            logger.info(f"Removing item '{item_name}' from inventory.")
                            items_to_remove.remove(
                                item_name
                            )  # Remove from set to handle multiples if needed
                            continue  # Skip adding this item back
                        new_inventory.append(item_dict)
                    current_inventory = new_inventory

                # Additions
                if effects.inventory_add:
                    for item_name_to_add in effects.inventory_add:
                        logger.info(f"Adding item '{item_name_to_add}' to inventory.")
                        # Check if item exists to increment quantity
                        found = False
                        for item_dict in current_inventory:
                            if (
                                item_dict.get("name", "").lower()
                                == item_name_to_add.lower()
                            ):
                                item_dict["quantity"] = item_dict.get("quantity", 0) + 1
                                found = True
                                break
                        if not found:
                            # Add new item - need default properties
                            # This is a simplification. Ideally, have an item database/template
                            new_item = ItemSchema(
                                id=f"item_{item_name_to_add.replace(' ','_').lower()}_{player.id}",  # Generate basic ID
                                name=item_name_to_add,
                                description="Acquired recently.",
                                quantity=1,
                                rarity="common",  # Default rarity
                            ).model_dump()  # Convert to dict for storage
                            current_inventory.append(new_item)

        player.inventory = current_inventory  # Assign back to trigger setter

    # --- Helper to Convert Backend Models to Frontend Schemas ---
    # These are crucial for matching the API response to frontend expectations

    def _map_player_to_schema(self, player: Player) -> PlayerStatsSchema:
        player_dict = player.to_dict()
        # Calculate maxXp based on level or use a fixed value if not implemented
        max_xp = 100 * player.level  # Example calculation
        return PlayerStatsSchema(
            currentHp=player_dict["currentHp"],
            maxHp=player_dict["maxHp"],
            gold=player_dict["gold"],
            xp=player_dict["xp"],
            maxXp=max_xp,
            level=player_dict["level"],
        )

    def _map_inventory_to_schema(
        self, inventory_list: List[Dict[str, Any]]
    ) -> List[ItemSchema]:
        items = []
        for item_data in inventory_list:
            # Add default values if keys are missing from the stored dict
            items.append(
                ItemSchema(
                    id=item_data.get("id", f"unknown_{item_data.get('name','item')}"),
                    name=item_data.get("name", "Unknown Item"),
                    description=item_data.get("description", ""),
                    quantity=item_data.get("quantity", 1),
                    rarity=item_data.get("rarity", "common"),
                    icon=item_data.get("icon"),
                    canUse=item_data.get(
                        "canUse", item_data.get("can_use")
                    ),  # Handle potential key variations
                    canEquip=item_data.get("canEquip", item_data.get("can_equip")),
                    canDrop=item_data.get("canDrop", item_data.get("can_drop")),
                )
            )
        return items

    def get_game_state_for_frontend(self, game_state: GameState) -> Dict[str, Any]:
        """Maps the backend GameState to the structure expected by the frontend."""
        if not game_state or not game_state.player:
            return {}  # Or raise error

        player_schema = self._map_player_to_schema(game_state.player)
        inventory_schema = self._map_inventory_to_schema(game_state.player.inventory)
        room_description = (game_state.current_room or {}).get(
            "description", "You are lost."
        )

        return {
            "playerStats": player_schema.model_dump(),
            "inventory": [item.model_dump() for item in inventory_schema],
            "description": room_description,
            # Add other fields from GameStateSchema if needed
        }
