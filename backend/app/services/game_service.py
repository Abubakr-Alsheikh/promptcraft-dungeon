# backend/app/services/game_service.py
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
                experience=0,  # Ensure XP starts at 0
            )
            game_state = GameState(
                player=player, difficulty=difficulty, rooms_cleared=0
            )

            # Prepare context *just* for initial room generation
            context = self._build_ai_context(game_state, command="<INITIAL_GENERATION>")

            # Generate the initial room description using the specific user prompt
            initial_room_ai_response: Optional[AIResponse] = (
                self.ai_service.generate_structured_response(
                    system_prompt_template=BASE_SYSTEM_PROMPT,
                    history=[],  # No history for the very first call
                    user_command=INITIAL_ROOM_PROMPT_USER.format(  # Format the specific user prompt part
                        player_name=player_name, difficulty=difficulty
                    ),
                    context=context,
                )
            )

            if (
                not initial_room_ai_response
                or not initial_room_ai_response.action_result_description
            ):
                logger.error("AI failed to generate initial room description.")
                return None, "Failed to generate the starting area with the Narrator."

            # Store initial room description (comes from action_result_description for the first call)
            initial_description = initial_room_ai_response.action_result_description
            initial_title = "The Beginning"  # Default title for the first room
            initial_exits = []  # AI *could* implicitly suggest exits in the description

            # Store the first room state
            game_state.current_room_json = json.dumps(
                {
                    "title": initial_title,
                    "description": initial_description,
                    "exits": initial_exits,
                    # Initial events might be specified by the AI, if any
                    "events": [
                        event.model_dump()
                        for event in initial_room_ai_response.triggered_events
                    ],
                }
            )
            logger.debug(f"Initial room generated: {initial_description[:100]}...")

            # --- Initialize Chat History ---
            # The AI's first output acts as the initial 'assistant' message providing the scene.
            initial_history = [
                # System prompt is added dynamically by AI Service now
                {
                    "role": "assistant",
                    "content": initial_room_ai_response.model_dump_json(),  # Store the full initial response
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
        Loads game state + history, sends command+context+history to AI,
        applies results, saves state + history, and handles room updates correctly.
        """
        logger.info(f"Handling command '{command}' for game state ID {game_state_id}")
        game_state: Optional[GameState] = None  # Initialize game_state
        try:
            game_state = db.session.get(GameState, game_state_id)
            if not game_state or not game_state.player:
                logger.error(f"Game state {game_state_id} not found or has no player.")
                return None, None, "Game session not found. Please start a new game."

            # Load existing chat history
            history = game_state.chat_history  # Use the getter
            logger.debug(
                f"Loaded history for game {game_state_id}, length: {len(history)}"
            )

            # Prepare Context for AI (used for formatting system prompt)
            context = self._build_ai_context(game_state, command)
            # logger.debug(f"AI Context: {context}") # Can be very verbose

            # Get AI Response
            ai_response: Optional[AIResponse] = (
                self.ai_service.generate_structured_response(
                    system_prompt_template=BASE_SYSTEM_PROMPT,
                    history=history,
                    user_command=command,
                    context=context,
                )
            )

            if not ai_response:
                logger.error(f"AI failed to generate response for command: {command}")
                # Don't save history if AI failed, return current state as is.
                return (
                    game_state,  # Return the state *before* the failed command
                    None,
                    "The Narrator seems lost in thought... (AI failed to respond)",
                )

            logger.debug(
                f"AI Response received: {ai_response.model_dump_json(indent=2)}"
            )

            # --- Update History BEFORE applying effects ---
            # Store the user command and the successful AI response JSON
            history.append({"role": "user", "content": command})
            history.append(
                {"role": "assistant", "content": ai_response.model_dump_json()}
            )
            game_state.chat_history = history  # Use the setter to save updated history

            # --- Apply AI-dictated changes to Game State ---
            self._apply_ai_effects(
                game_state.player, ai_response
            )  # Apply effects first

            # --- Update Room State (Crucial Change Here) ---
            current_room_data = game_state.current_room or {}  # Get mutable dict

            # Check if the AI response indicates a move to a NEW room
            if ai_response.room_description:  # Check the RENAMED field
                logger.info(
                    f"Player is moving to a new room/area in game {game_state_id}"
                )
                current_room_data["description"] = (
                    ai_response.room_description
                )  # Update with the new description
                current_room_data["title"] = (
                    ai_response.new_room_title or "Unknown Area"
                )  # Use AI suggested title or default
                current_room_data["exits"] = (
                    ai_response.new_room_exits or []
                )  # Use AI suggested exits or reset
                # Events triggered by the *action* that caused the move are already captured in ai_response.triggered_events
                # We might want to clear room-specific events upon moving, or let the AI define new ones for the room
                current_room_data["events"] = (
                    []
                )  # Clear old room-specific events? Or keep action-related ones? Decision needed. Let's clear for now.
                # Alternatively, filter ai_response.triggered_events for only those relevant *after* the move? Complex.
                game_state.rooms_cleared += (
                    1  # Increment if moving counts as clearing previous area
                )
            else:
                # Player remains in the same room. DO NOT overwrite the main description.
                # The 'action_result_description' is for immediate feedback, not the persistent room state.
                # We *could* update room 'events' based on the action's triggered events, if needed.
                # For example, if an action revealed a hidden switch in the current room.
                logger.debug(
                    f"Player remains in room '{current_room_data.get('title', 'current')}'"
                )
                # Decide if action-triggered events should modify the *room's* persistent event list
                # For now, let's assume room events are relatively static unless AI explicitly modifies them via a dedicated event type.
                # current_room_data["events"] = [event.model_dump() for event in ai_response.triggered_events] # This would make room events reflect the last action heavily. Maybe not desired.

            game_state.current_room = current_room_data  # Assign back to trigger setter

            # Save Updated State (includes updated history, player stats, room state)
            db.session.commit()
            logger.info(
                f"Game state {game_state_id} updated and saved after command '{command}'. History length: {len(history)}"
            )

            # Return the updated state and the full AI response
            return game_state, ai_response, None

        except Exception as e:
            db.session.rollback()
            logger.exception(
                f"Error handling command '{command}' for game state {game_state_id}: {e}"
            )
            # If an exception occurred after loading state but before finishing,
            # it's safer to return None than potentially inconsistent state.
            # If game_state was loaded, we *could* try returning it, but risk inconsistency.
            # Let's return None for state on major errors.
            return None, None, f"An unexpected server error occurred: {e}"

    def _build_ai_context(self, game_state: GameState, command: str) -> Dict[str, Any]:
        """Helper to create the context dictionary for AI system prompts."""
        player = game_state.player
        room = game_state.current_room or {
            "description": "An empty void",
            "exits": [],
            "title": "Nowhere",
        }

        inventory_list = []
        for item_dict in player.inventory:
            name = item_dict.get("name", "Unknown Item")
            qty = item_dict.get("quantity", 1)
            inventory_list.append(f"{name} ({qty})")
        inventory_str = ", ".join(inventory_list) if inventory_list else "Empty"

        context = {
            "difficulty": game_state.difficulty,
            "player_name": player.name,
            "health": player.health,
            "max_health": player.max_health,
            "level": player.level,
            "inventory": inventory_str,
            # Provide the persistent room description here
            "current_room_description": room.get(
                "description", "You are in a featureless location."
            ),
            # Provide known exits
            "current_room_exits": ", ".join(room.get("exits", [])),
            "player_command": command,  # The *current* command being processed
        }
        return context

    def _apply_ai_effects(self, player: Player, ai_response: AIResponse):
        """Applies effects from AI events to the player state."""
        if not player:
            logger.warning("Attempted to apply effects to a null player.")
            return

        # Use a temporary variable to hold inventory for modification clarity
        current_inventory = list(player.inventory)  # Ensure it's a mutable list copy

        for event in ai_response.triggered_events:
            if event.effects:
                effects = event.effects
                logger.debug(
                    f"Applying effects from event type '{event.type}': {effects.model_dump()}"
                )

                # Health changes
                if effects.health is not None:  # Check for None explicitly
                    try:
                        delta = int(effects.health)
                        new_health = max(
                            0, min(player.max_health, player.health + delta)
                        )
                        if new_health != player.health:
                            logger.info(
                                f"Player health changed by {delta} from {player.health} to {new_health}"
                            )
                            player.health = new_health
                        else:
                            logger.debug(
                                f"Health change {delta} resulted in no actual change (min/max boundary)."
                            )
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid health effect value: {effects.health}")

                # Gold changes
                if effects.gold is not None:
                    try:
                        delta = int(effects.gold)
                        new_gold = max(0, player.gold + delta)
                        if new_gold != player.gold:
                            logger.info(
                                f"Player gold changed by {delta} from {player.gold} to {new_gold}"
                            )
                            player.gold = new_gold
                        else:
                            logger.debug(
                                f"Gold change {delta} resulted in no actual change (min 0)."
                            )
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid gold effect value: {effects.gold}")

                # XP changes
                if effects.xp is not None:
                    try:
                        delta = int(effects.xp)
                        if delta > 0:  # Typically only gain XP
                            new_xp = player.experience + delta
                            logger.info(
                                f"Player XP changed by {delta} from {player.experience} to {new_xp}"
                            )
                            player.experience = new_xp
                            # TODO: Add level up check logic here
                            # if player.experience >= calculate_xp_for_next_level(player.level):
                            #    level_up(player)
                        elif delta < 0:
                            logger.warning(
                                f"Received negative XP change ({delta}), ignoring."
                            )
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid XP effect value: {effects.xp}")

                # Inventory changes - Removals first
                if effects.inventory_remove:
                    items_to_remove_lower = {
                        item_name.lower().strip()
                        for item_name in effects.inventory_remove
                        if item_name  # Ignore empty strings
                    }
                    if not items_to_remove_lower:
                        continue  # Skip if list was empty/invalid

                    next_inventory = []
                    items_actually_removed = set()
                    for item_dict in current_inventory:
                        item_name = item_dict.get("name", "").lower().strip()
                        if item_name in items_to_remove_lower:
                            # Simple removal - assumes quantity 1 or remove whole stack
                            # TODO: Implement quantity-based removal if needed
                            logger.info(
                                f"Removing item '{item_dict.get('name', item_name)}' from inventory."
                            )
                            items_to_remove_lower.remove(
                                item_name
                            )  # Remove from set to handle only first match if names collide (shouldn't happen with unique IDs ideally)
                            items_actually_removed.add(item_dict.get("name", item_name))
                            # Don't add this item back to next_inventory
                            continue
                        next_inventory.append(item_dict)
                    current_inventory = (
                        next_inventory  # Update the list being worked on
                    )

                    # Log if some requested items weren't found
                    for requested_remove in effects.inventory_remove:
                        if requested_remove not in items_actually_removed:
                            logger.warning(
                                f"Attempted to remove item '{requested_remove}', but it was not found in inventory."
                            )

                # Inventory changes - Additions
                if effects.inventory_add:
                    for item_name_to_add in effects.inventory_add:
                        if not item_name_to_add or not item_name_to_add.strip():
                            continue  # Skip empty names

                        item_name_to_add = item_name_to_add.strip()  # Clean name
                        logger.info(f"Adding item '{item_name_to_add}' to inventory.")

                        # Check if item exists to increment quantity (case-insensitive check)
                        found = False
                        for item_dict in current_inventory:
                            if (
                                item_dict.get("name", "").strip().lower()
                                == item_name_to_add.lower()
                            ):
                                item_dict["quantity"] = item_dict.get("quantity", 0) + 1
                                logger.debug(
                                    f"Incremented quantity for '{item_name_to_add}' to {item_dict['quantity']}"
                                )
                                found = True
                                break
                        if not found:
                            # Add new item - need default properties
                            # This is a simplification. Ideally, have an item template/database lookup
                            # Use Pydantic schema to create the dict, ensuring structure
                            new_item_schema = ItemSchema(
                                # Generate a more robust unique ID if possible, maybe using uuid
                                id=f"item_{item_name_to_add.replace(' ','_').lower()}_{player.id}_{len(current_inventory)}",
                                name=item_name_to_add,
                                description="Acquired recently.",  # AI could potentially provide description
                                quantity=1,
                                rarity="common",  # Default rarity, AI could specify
                                # Default other fields from ItemSchema
                                icon=None,
                                canUse=False,  # Defaults, AI could specify based on item type
                                canEquip=False,
                                canDrop=True,
                            )
                            current_inventory.append(
                                new_item_schema.model_dump()
                            )  # Add as dict
                            logger.debug(
                                f"Added new item entry: {new_item_schema.model_dump()}"
                            )

                # TODO: Apply status effects (add/remove) to player state if needed
                # Requires player model to have a status effects field (e.g., JSON list)
                # if effects.status_effect_add: player.add_status_effects(effects.status_effect_add)
                # if effects.status_effect_remove: player.remove_status_effects(effects.status_effect_remove)

        # Assign the modified list back to the player property to trigger the setter
        player.inventory = current_inventory
        logger.debug("Finished applying AI effects.")

    def _map_player_to_schema(self, player: Player) -> PlayerStatsSchema:
        """Maps the backend Player model to the PlayerStatsSchema for frontend."""
        if not player:  # Defensive check
            # Return a default/empty schema or raise error?
            logger.error("Cannot map null player to schema.")
            # Returning default schema to avoid breaking API contract, but indicates an issue.
            return PlayerStatsSchema(
                currentHp=0, maxHp=0, gold=0, xp=0, maxXp=100, level=1
            )

        # Example XP calculation for next level (adjust as needed)
        max_xp = 100 * (2 ** (player.level - 1))  # Exponential growth example

        # Use Pydantic model for validation and structure
        try:
            player_schema = PlayerStatsSchema(
                currentHp=player.health,
                maxHp=player.max_health,
                gold=player.gold,
                xp=player.experience,
                maxXp=max_xp,
                level=player.level,
            )
            return player_schema
        except Exception as e:  # Catch potential validation errors during creation
            logger.error(
                f"Error mapping player data to PlayerStatsSchema: {e}. Data: {player.to_dict()}"
            )
            # Return default again or re-raise? Default prevents crash.
            return PlayerStatsSchema(
                currentHp=0, maxHp=0, gold=0, xp=0, maxXp=100, level=1
            )

    def _map_inventory_to_schema(
        self, inventory_list: List[Dict[str, Any]]
    ) -> List[ItemSchema]:
        """Maps the backend inventory (list of dicts) to a list of ItemSchema for frontend."""
        items_schema_list = []
        if not isinstance(inventory_list, list):  # Basic type check
            logger.error(
                f"Invalid inventory data type for mapping: {type(inventory_list)}"
            )
            return []

        for item_data in inventory_list:
            if not isinstance(item_data, dict):  # Ensure item is a dict
                logger.warning(f"Skipping invalid item data in inventory: {item_data}")
                continue
            try:
                # Use ItemSchema.model_validate for robust validation and default handling
                item_schema = ItemSchema.model_validate(
                    {
                        # Provide defaults explicitly if keys might be missing entirely
                        "id": item_data.get(
                            "id",
                            f"unknown_{item_data.get('name','item')}_{len(items_schema_list)}",
                        ),  # More robust default ID
                        "name": item_data.get("name", "Unknown Item"),
                        "description": item_data.get("description", ""),
                        "quantity": item_data.get("quantity", 1),
                        "rarity": item_data.get("rarity", "common"),
                        "icon": item_data.get("icon"),
                        # Handle potential key variations ('canUse' vs 'can_use') gracefully
                        "canUse": item_data.get(
                            "canUse", item_data.get("can_use", False)
                        ),
                        "canEquip": item_data.get(
                            "canEquip", item_data.get("can_equip", False)
                        ),
                        "canDrop": item_data.get(
                            "canDrop", item_data.get("can_drop", True)
                        ),  # Default to True?
                    }
                )
                items_schema_list.append(item_schema)
            except Exception as e:  # Catch validation errors for individual items
                logger.error(
                    f"Error mapping item data to ItemSchema: {e}. Data: {item_data}"
                )
                # Optionally append a placeholder or skip the item
        return items_schema_list

    def get_game_state_for_frontend(self, game_state: GameState) -> Dict[str, Any]:
        """Maps the backend GameState to the structure expected by the frontend API response."""
        if not game_state or not game_state.player:
            logger.error("Cannot get frontend state for null GameState or Player.")
            # Return an empty dict or structure matching frontend expectation but with error state?
            # Let's return empty for now, caller should handle this.
            return {}

        player_schema = self._map_player_to_schema(game_state.player)
        inventory_schema = self._map_inventory_to_schema(game_state.player.inventory)
        current_room = game_state.current_room or {}
        room_description = current_room.get("description", "You are lost in the void.")
        room_title = current_room.get("title", "Unknown Location")

        # Structure matches parts of GetStateResponse and InitialStateResponse schemas
        return {
            "playerStats": player_schema.model_dump(),
            "inventory": [item.model_dump() for item in inventory_schema],
            "description": room_description,  # The persistent room description
            "roomTitle": room_title,  # Add room title
            # Add other fields relevant to frontend state if needed
            # "available_exits": current_room.get("exits", []), # If frontend needs exits explicitly
        }
