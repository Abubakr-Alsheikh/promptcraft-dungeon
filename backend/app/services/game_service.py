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
        Initializes a new game state, generates the first room via AI, saves state and initial history.
        """
        logger.info(f"Starting new game for {player_name}, difficulty {difficulty}")
        try:
            player = Player(
                name=player_name,
                health=100,
                max_health=100,
                inventory=[],
                level=1,
                gold=10,
            )
            game_state = GameState(
                player=player, difficulty=difficulty, rooms_cleared=0
            )

            # Prepare context *just* for initial room generation
            context = self._build_ai_context(
                game_state, command="<INITIAL_GENERATION>"
            )  # Special command context

            # Generate the initial room using a *separate call* to the AI
            # We don't have history yet for this first call.
            initial_room_ai_response: Optional[AIResponse] = (
                self.ai_service.generate_structured_response(
                    system_prompt_template=BASE_SYSTEM_PROMPT,  # Use the main system prompt
                    history=[],  # No history for the very first call
                    user_command=INITIAL_ROOM_PROMPT_USER.format(  # Format the user prompt part
                        player_name=player_name, difficulty=difficulty
                    ),
                    context=context,  # Pass context for system prompt formatting
                )
            )

            if not initial_room_ai_response:
                logger.error("AI failed to generate initial room.")
                return None, "Failed to generate the starting area with AI."

            # Store initial room description
            initial_description = initial_room_ai_response.action_result_description
            game_state.current_room_json = json.dumps(
                {
                    "title": "Beginning",
                    "description": initial_description,
                    "exits": [],  # AI could potentially suggest exits in initial response
                    "events": [
                        event.model_dump()
                        for event in initial_room_ai_response.triggered_events
                    ],
                }
            )
            logger.debug(f"Initial room generated: {initial_description[:100]}...")

            # --- Initialize Chat History ---
            # Store the system prompt used and the AI's first response.
            # We *don't* store the INITIAL_ROOM_PROMPT_USER itself, as it's not a typical user command.
            # The AI's first output acts as the initial 'assistant' message.
            formatted_system_prompt = self.ai_service._format_system_prompt(
                BASE_SYSTEM_PROMPT, context
            )
            initial_history = [
                # System prompt is added dynamically by AI Service now, so history starts with assistant
                # {'role': 'system', 'content': formatted_system_prompt}, # Optional: Store the first system prompt?
                {
                    "role": "assistant",
                    "content": initial_room_ai_response.model_dump_json(),
                }
            ]
            game_state.chat_history = initial_history  # Use the setter

            db.session.add(game_state)
            db.session.commit()
            logger.info(
                f"New game state (ID: {game_state.id}) created and saved with initial history."
            )

            return game_state, None

        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error starting new game: {e}")
            return None, f"An unexpected server error occurred: {e}"

    def handle_player_command(
        self, game_state_id: int, command: str
    ) -> Tuple[Optional[GameState], Optional[AIResponse], Optional[str]]:
        """
        Loads game state + history, sends command+context+history to AI, applies results, saves state + history.
        """
        logger.info(f"Handling command '{command}' for game state ID {game_state_id}")
        try:
            game_state: Optional[GameState] = db.session.get(GameState, game_state_id)
            if not game_state or not game_state.player:
                logger.error(f"Game state {game_state_id} not found or has no player.")
                return None, None, "Game session not found. Please start a new game."

            # Load existing chat history
            history = game_state.chat_history  # Use the getter
            print(history)

            # Prepare Context for AI (used for formatting system prompt)
            context = self._build_ai_context(game_state, command)
            logger.debug(f"AI Context: {context}")

            # Get AI Response, passing history and current command
            ai_response: Optional[AIResponse] = (
                self.ai_service.generate_structured_response(
                    system_prompt_template=BASE_SYSTEM_PROMPT,
                    history=history,  # Pass the loaded history
                    user_command=command,  # Pass the raw user command
                    context=context,  # Pass context for system prompt formatting
                )
            )

            if not ai_response:
                logger.error(f"AI failed to generate response for command: {command}")
                # Even if AI fails, save the user command attempt in history? Optional.
                # history.append({'role': 'user', 'content': command})
                # game_state.chat_history = history
                # db.session.commit() # Commit the added user message
                return (
                    game_state,
                    None,
                    "The Narrator seems lost in thought... (AI failed to respond)",
                )

            logger.debug(
                f"AI Response received: {ai_response.model_dump_json(indent=2)}"
            )

            # --- IMPORTANT: Update History BEFORE applying effects ---
            # Store the user command and the successful AI response JSON
            history.append({"role": "user", "content": command})
            history.append(
                {"role": "assistant", "content": ai_response.model_dump_json()}
            )
            game_state.chat_history = history  # Use the setter to save updated history

            # Apply AI-dictated changes to Game State
            self._apply_ai_effects(game_state.player, ai_response)

            # Update room description / Handle potential room change
            current_room_data = game_state.current_room or {}
            if ai_response.new_room_description:
                logger.info(f"Moving to new room for game {game_state_id}")
                current_room_data["description"] = ai_response.new_room_description
                current_room_data["title"] = (
                    "New Area"  # Or extract from AI response if possible
                )
                current_room_data["exits"] = []  # Reset exits? Or expect AI to provide?
                # Events from the AI response likely relate to the *action*, not the *new room itself*.
                # Keep the events triggered by the action that *led* to the new room.
                current_room_data["events"] = [
                    event.model_dump() for event in ai_response.triggered_events
                ]
                game_state.rooms_cleared += 1
            else:
                # The primary description of the action's result *is* the new situation description
                current_room_data["description"] = ai_response.action_result_description
                current_room_data["events"] = [
                    event.model_dump() for event in ai_response.triggered_events
                ]

            game_state.current_room = current_room_data

            # Save Updated State (includes updated history, player stats, room state)
            db.session.commit()
            logger.info(
                f"Game state {game_state_id} updated and saved after command '{command}'. History length: {len(history)}"
            )

            return game_state, ai_response, None

        except Exception as e:
            db.session.rollback()
            logger.exception(
                f"Error handling command '{command}' for game state {game_state_id}: {e}"
            )
            # Attempt to return last known state? The state object might be inconsistent here.
            # Best to return None for state to avoid sending potentially corrupt data.
            return None, None, f"An unexpected server error occurred: {e}"

    # --- _build_ai_context remains largely the same ---
    # It provides *current snapshot* context for the system prompt, not history.
    def _build_ai_context(self, game_state: GameState, command: str) -> Dict[str, Any]:
        """Helper to create the context dictionary for AI system prompts."""
        player = game_state.player
        room = game_state.current_room or {"description": "An empty void", "exits": []}

        inventory_list = []
        for item_dict in player.inventory:
            name = item_dict.get("name", "Unknown Item")
            qty = item_dict.get("quantity", 1)
            inventory_list.append(f"{name} ({qty})")
        inventory_str = ", ".join(inventory_list) if inventory_list else "Empty"

        # Only include keys expected by BASE_SYSTEM_PROMPT format()
        context = {
            "difficulty": game_state.difficulty,
            "player_name": player.name,
            "health": player.health,
            "max_health": player.max_health,
            "level": player.level,
            "inventory": inventory_str,
            "current_room_description": room.get(
                "description", "You are in a featureless location."
            ),
            "current_room_exits": ", ".join(room.get("exits", [])),
            "player_command": command,  # The *current* command being processed
        }
        # logger.debug(f"Built context for AI: {context}") # Optional: very verbose
        return context

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
