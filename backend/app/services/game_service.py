import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from ..extensions import db
from ..models.game import GameState, Player, Item, PlayerInventoryItem
from ..schemas.ai_responses import AIResponse
from ..prompts.game_prompts import BASE_SYSTEM_PROMPT, INITIAL_ROOM_PROMPT_USER
from ..schemas.game import PlayerStatsSchema, ItemSchema  # Pydantic schemas for API
from ..services.ai_service import AIService, AIResponseError

logger = logging.getLogger(__name__)


class GameServiceError(Exception):
    """Custom exception for Game Service errors."""

    pass


class GameService:
    """
    Handles the core game logic, state management, and interactions between
    the database, AI service, and API routes.
    """

    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service

    def start_new_game(
        self, player_name: str, difficulty: str
    ) -> Tuple[Optional[GameState], Optional[str]]:
        """
        Initializes a new game: creates Player & GameState, gets the first
        room description from AI, saves initial state and chat history.

        Returns:
            Tuple (GameState object, None) on success.
            Tuple (None, error_message) on failure.
        """
        logger.info(
            f"Attempting to start new game for player '{player_name}', difficulty '{difficulty}'"
        )
        try:
            # 1. Create Player and GameState objects (without saving yet)
            player = Player(name=player_name, gold=10)  # Defaults set in model
            game_state = GameState(player=player, difficulty=difficulty)
            # Add to session early so relationships can work if needed immediately
            db.session.add(game_state)
            # Flush to get IDs assigned, but don't commit yet
            db.session.flush()
            logger.debug(
                f"Created initial Player ID: {player.id}, GameState ID: {game_state.id}"
            )

            # 2. Prepare context for initial AI room generation
            context = self._build_ai_context(game_state, command="<INITIAL_GENERATION>")
            initial_user_prompt = INITIAL_ROOM_PROMPT_USER.format(
                player_name=player.name, difficulty=game_state.difficulty
            )

            # 3. Call AI Service to generate the first scene
            initial_ai_response, ai_error = (
                self.ai_service.generate_structured_response(
                    system_prompt_template=BASE_SYSTEM_PROMPT,
                    history=[],  # No history for the very first call
                    user_command=initial_user_prompt,
                    context=context,
                )
            )

            if ai_error or not initial_ai_response:
                error_msg = (
                    f"AI failed to generate initial room: {ai_error or 'No response'}"
                )
                logger.error(error_msg)
                # Rollback changes if AI fails startup
                db.session.rollback()
                return None, error_msg

            # Ensure essential part of response is present
            if not initial_ai_response.action_result_description:
                error_msg = "AI response for initial room lacked essential 'action_result_description'."
                logger.error(error_msg)
                db.session.rollback()
                return None, error_msg

            logger.debug("AI generated initial room successfully.")

            # 4. Set the initial room state based on AI response
            initial_description = initial_ai_response.action_result_description
            initial_title = initial_ai_response.new_room_title or "The Beginning"
            initial_exits = initial_ai_response.new_room_exits or []
            # Use the setter for current_room
            game_state.current_room = {
                "title": initial_title,
                "description": initial_description,
                "exits": initial_exits,
                "events": [
                    evt.model_dump() for evt in initial_ai_response.triggered_events
                ],
            }
            logger.debug(f"Initial room set: '{initial_title}'")

            # 5. Initialize Chat History with the AI's first message
            # Store the structured AI response as a JSON string in the content
            initial_ai_content_json = initial_ai_response.model_dump_json()
            game_state.add_chat_message(
                role="assistant",
                content=initial_ai_content_json,
                turn_number=0,  # First turn (AI introduces scene)
            )
            logger.debug("Initial chat history added.")

            # 6. Apply any effects from initial AI response (e.g., maybe AI gives starting item)
            # This is unlikely for initial prompt but possible
            self._apply_ai_effects(player, initial_ai_response)

            # 7. Commit the entire transaction
            db.session.commit()
            logger.info(
                f"New game (ID: {game_state.id}) started successfully for player '{player.name}'."
            )

            return game_state, None

        except Exception as e:
            db.session.rollback()
            logger.exception(f"Unexpected error starting new game: {e}")
            return (
                None,
                f"An unexpected server error occurred during game creation: {e}",
            )

    def handle_player_command(
        self, game_state_id: int, command: str
    ) -> Tuple[Optional[GameState], Optional[AIResponse], Optional[str]]:
        """
        Processes a player command: loads state, calls AI, applies results, saves state.

        Returns:
            Tuple (updated GameState, AIResponse, None) on success.
            Tuple (original GameState | None, None, error_message) on failure.
        """
        logger.info(f"Handling command '{command}' for game ID {game_state_id}")
        game_state: Optional[GameState] = None
        try:
            # 1. Load Game State and Player (with necessary relationships)
            # Use joinedload/selectinload for efficiency if accessing relationships often
            game_state = db.session.get(
                GameState,
                game_state_id,
                options=[
                    selectinload(GameState.player)
                    .selectinload(Player.inventory_items)
                    .joinedload(PlayerInventoryItem.item),
                    selectinload(GameState.chat_messages),  # Load history efficiently
                ],
            )

            if not game_state or not game_state.player:
                logger.error(f"Game state {game_state_id} not found or has no player.")
                return None, None, "Game session not found. Please start a new game."

            player = game_state.player
            logger.debug(f"Loaded game state for player '{player.name}'.")

            # 2. Get chat history formatted for AI
            history = game_state.get_chat_history_for_ai()
            current_turn = len(history)  # Next turn number (0-indexed)
            logger.debug(f"History length for AI: {len(history)}")

            # 3. Prepare Context & Call AI Service
            context = self._build_ai_context(game_state, command)
            ai_response, ai_error = self.ai_service.generate_structured_response(
                system_prompt_template=BASE_SYSTEM_PROMPT,
                history=history,
                user_command=command,
                context=context,
            )

            # 4. Handle AI Failure
            if ai_error or not ai_response:
                error_msg = f"AI interaction failed: {ai_error or 'No response'}"
                logger.error(
                    f"{error_msg} for game {game_state_id}, command '{command}'"
                )
                # Do NOT commit any changes. Return the state *before* the failed command attempt.
                # Do NOT add the failed command/response to history.
                return game_state, None, error_msg  # Return original state

            logger.debug(f"AI Response received for command '{command}'.")
            # logger.debug(f"AI Response data: {ai_response.model_dump_json(indent=2)}")

            # --- If AI Success, proceed with updates ---

            # 5. Add User Command and AI Response to Chat History
            game_state.add_chat_message(
                role="user", content=command, turn_number=current_turn
            )
            game_state.add_chat_message(
                role="assistant",
                content=ai_response.model_dump_json(),
                turn_number=current_turn + 1,
            )
            logger.debug(
                f"Added user command and AI response to history for turn {current_turn}."
            )

            # 6. Apply AI Effects to Player State
            self._apply_ai_effects(player, ai_response)
            logger.debug("Applied AI effects to player state.")

            # 7. Update Room State if Necessary
            current_room_data = game_state.current_room or {}  # Get mutable dict
            if ai_response.room_description:  # AI indicates a move to a NEW room
                logger.info(
                    f"Player moving to new area in game {game_state_id}. AI Title: '{ai_response.new_room_title}'"
                )
                new_title = ai_response.new_room_title or "Unknown Area"
                game_state.current_room = {
                    "title": new_title,
                    "description": ai_response.room_description,
                    "exits": ai_response.new_room_exits or [],
                    "events": [],  # Reset room-specific events upon entering a new one? Or use triggered_events? Simple reset for now.
                }
                game_state.rooms_cleared += (
                    1  # Increment counter for moving to new area
                )
                logger.debug(
                    f"Updated current_room to '{new_title}'. Rooms cleared: {game_state.rooms_cleared}"
                )
            else:
                # Player remains in the same room. Only the AI's 'action_result_description' provides feedback.
                # The persistent 'current_room.description' is NOT updated here.
                # We *could* potentially update the room's 'events' list based on ai_response.triggered_events
                # if an action modified the current room (e.g., revealed something). Requires careful design.
                logger.debug(
                    f"Player remains in room '{current_room_data.get('title', 'current')}'"
                )
                # No change needed to game_state.current_room property itself if description isn't changing.

            # 8. Commit all changes (history, player state, room state)
            db.session.commit()
            logger.info(
                f"Game state {game_state_id} updated successfully after command '{command}'."
            )

            # 9. Return updated state and the successful AI response
            return game_state, ai_response, None

        except Exception as e:
            db.session.rollback()  # Rollback on any unexpected error during processing
            logger.exception(
                f"Unexpected error handling command '{command}' for game {game_state_id}: {e}"
            )
            # Return None for state to indicate a critical failure. The route handler should signal 500.
            return None, None, f"An unexpected server error occurred: {e}"

    def _build_ai_context(self, game_state: GameState, command: str) -> Dict[str, Any]:
        """Helper to create the context dictionary for AI system prompts."""
        player = game_state.player
        room = game_state.current_room or {}  # Use property getter

        # Fetch inventory details using the relationship
        inventory_list = []
        # Ensure items are loaded - they should be if using eager loading in handle_player_command
        if player and player.inventory_items:
            # Access related item details via the relationship
            for inv_item in player.inventory_items:
                if inv_item.item:  # Check if item relationship loaded
                    name = inv_item.item.name
                    qty = inv_item.quantity
                    inventory_list.append(f"{name} (x{qty})")
                else:
                    logger.warning(
                        f"Inventory item entry missing related Item data for player {player.id}"
                    )
        inventory_str = ", ".join(inventory_list) if inventory_list else "Empty"

        context = {
            "difficulty": game_state.difficulty,
            "player_name": player.name if player else "Unknown",
            "health": player.health if player else 0,
            "max_health": player.max_health if player else 0,
            "level": player.level if player else 0,
            "gold": player.gold if player else 0,
            "inventory": inventory_str,
            "current_room_title": room.get("title", "Unknown Location"),
            "current_room_description": room.get(
                "description", "You are in a featureless location."
            ),
            "current_room_exits": ", ".join(room.get("exits", [])),
            "player_command": command,
        }
        return context

    def _apply_ai_effects(self, player: Player, ai_response: AIResponse):
        """
        Applies effects from AIResponse triggered_events to the player state.
        Modifies the player object directly (assumes active db session).
        """
        if not player:
            logger.warning("Attempted to apply effects to a null player.")
            return

        logger.debug(f"Applying effects for player {player.id}...")
        items_cache = (
            {}
        )  # Simple cache to avoid repeated DB lookups for the same item key in one response

        for event in ai_response.triggered_events:
            if not event.effects:
                continue  # Skip events with no effects block

            effects = event.effects
            logger.debug(
                f"Processing effects from event type '{event.type}': {effects.model_dump()}"
            )

            # --- Stat Changes ---
            try:
                if effects.health is not None:
                    delta = int(effects.health)
                    player.health = max(
                        0, min(player.max_health, player.health + delta)
                    )
                    logger.debug(
                        f"Player {player.id} health changed by {delta} to {player.health}"
                    )
                if effects.gold is not None:
                    delta = int(effects.gold)
                    player.gold = max(0, player.gold + delta)
                    logger.debug(
                        f"Player {player.id} gold changed by {delta} to {player.gold}"
                    )
                if effects.xp is not None:
                    delta = int(effects.xp)
                    if delta > 0:
                        player.experience += delta
                        logger.debug(
                            f"Player {player.id} XP changed by {delta} to {player.experience}"
                        )
                        # TODO: Implement level up check
                        # self._check_level_up(player)
                    elif delta < 0:
                        logger.warning(
                            f"Ignoring negative XP change ({delta}) for player {player.id}"
                        )
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"Invalid numeric value in effects for player {player.id}: {e}. Effect: {effects.model_dump()}"
                )

            # --- Inventory Removals ---
            if effects.inventory_remove:
                items_removed_count = 0
                for item_name_to_remove in effects.inventory_remove:
                    item_name_lower = item_name_to_remove.lower().strip()
                    if not item_name_lower:
                        continue

                    # Find the inventory item entry matching the name (case-insensitive)
                    found_entry: Optional[PlayerInventoryItem] = None
                    for inv_item in player.inventory_items:
                        if (
                            inv_item.item
                            and inv_item.item.name.lower() == item_name_lower
                        ):
                            found_entry = inv_item
                            break

                    if found_entry:
                        # Simple removal: decrease quantity or delete entry
                        if found_entry.quantity > 1:
                            found_entry.quantity -= 1
                            logger.debug(
                                f"Decremented quantity for item '{found_entry.item.name}' to {found_entry.quantity} for player {player.id}"
                            )
                        else:
                            # Remove the association object from the session
                            db.session.delete(found_entry)
                            # Important: Also remove from the player's loaded collection to reflect change immediately
                            # This requires the relationship to be loaded and mutable.
                            # player.inventory_items.remove(found_entry) # Might cause issues depending on cascade/session state
                            logger.debug(
                                f"Removed item entry '{found_entry.item.name}' for player {player.id}"
                            )
                        items_removed_count += 1
                        # Break if only removing one instance, continue if removing all matching items by name is intended
                    else:
                        logger.warning(
                            f"Player {player.id} tried to remove item '{item_name_to_remove}', but it wasn't found in inventory."
                        )
                if items_removed_count > 0:
                    db.session.flush()  # Flush removals before additions if needed

            # --- Inventory Additions ---
            if effects.inventory_add:
                items_added_count = 0
                for item_name_to_add in effects.inventory_add:
                    item_name_clean = item_name_to_add.strip()
                    if not item_name_clean:
                        continue
                    item_key = item_name_clean.lower().replace(
                        " ", "_"
                    )  # Simple key generation, **fragile**

                    # TODO: Robust Item Handling - This assumes AI provides names that map directly
                    # to existing Item.name or Item.item_key. Ideally, AI should provide a predefined
                    # item_key, or we need a lookup system (e.g., fuzzy matching name -> item_key).

                    # 1. Find the base Item definition
                    item_def: Optional[Item] = items_cache.get(item_key)
                    if not item_def:
                        # Try finding by key, then maybe by name (case-insensitive)
                        stmt = select(Item).where(
                            (Item.item_key == item_key)
                            | (Item.name.ilike(item_name_clean))
                        )
                        item_def = db.session.execute(stmt).scalar_one_or_none()
                        if item_def:
                            items_cache[item_key] = item_def  # Cache it

                    if not item_def:
                        # Option 1: Fail - Item must exist in DB
                        logger.warning(
                            f"Item definition not found for '{item_name_to_add}' (key: '{item_key}'). Cannot add to inventory for player {player.id}."
                        )
                        # Option 2: Create a basic item on the fly (less controlled)
                        # logger.info(f"Creating basic item definition for '{item_name_to_add}' on the fly.")
                        # item_def = Item(item_key=item_key, name=item_name_to_add, description="Newly discovered.")
                        # db.session.add(item_def)
                        # db.session.flush() # Get ID
                        # items_cache[item_key] = item_def
                        continue  # Skip adding if definition not found (Option 1)

                    # 2. Check if player already has this item type
                    existing_entry: Optional[PlayerInventoryItem] = None
                    for inv_item in player.inventory_items:
                        if inv_item.item_id == item_def.id:
                            existing_entry = inv_item
                            break

                    # 3. Add or update inventory entry
                    if existing_entry:
                        existing_entry.quantity += 1
                        logger.debug(
                            f"Incremented quantity for item '{item_def.name}' to {existing_entry.quantity} for player {player.id}"
                        )
                    else:
                        new_entry = PlayerInventoryItem(
                            player_id=player.id, item_id=item_def.id, quantity=1
                        )
                        db.session.add(new_entry)  # Add the new association
                        # Also add to loaded relationship if needed for immediate access before commit/refresh
                        player.inventory_items.append(new_entry)
                        logger.debug(
                            f"Added new item '{item_def.name}' (qty 1) for player {player.id}"
                        )
                    items_added_count += 1
                if items_added_count > 0:
                    db.session.flush()  # Flush additions

            # --- Status Effects ---
            # TODO: Implement status effect handling if Player model has status field
            # if effects.status_effect_add: logger.info(f"Adding status effects: {effects.status_effect_add}") # player.add_status(effects.status_effect_add)
            # if effects.status_effect_remove: logger.info(f"Removing status effects: {effects.status_effect_remove}") # player.remove_status(effects.status_effect_remove)

        logger.debug(f"Finished applying effects for player {player.id}.")
        # No explicit commit here, handled by caller (handle_player_command)

    # --- Mapping Functions to Frontend Schemas ---

    def get_game_state_for_frontend(
        self, game_state: GameState
    ) -> Optional[Dict[str, Any]]:
        """
        Maps the backend GameState to the dictionary structure expected by frontend API responses.
        Uses Pydantic schemas for player stats and inventory items.

        Returns:
            Dictionary matching frontend expectations, or None if mapping fails.
        """
        if not game_state or not game_state.player:
            logger.error("Cannot get frontend state for null GameState or Player.")
            return None

        try:
            player_schema = self._map_player_to_schema(game_state.player)
            # Ensure inventory items and their related item details are loaded
            inventory_schema_list = self._map_inventory_to_schema(
                game_state.player.inventory_items
            )

            current_room = game_state.current_room  # Use property
            room_description = (
                current_room.get("description", "Error: Room data missing.")
                if current_room
                else "You are in an undefined space."
            )
            room_title = (
                current_room.get("title", "Unknown Location")
                if current_room
                else "Nowhere"
            )

            return {
                "playerStats": player_schema.model_dump(),
                "inventory": [item.model_dump() for item in inventory_schema_list],
                "description": room_description,
                "roomTitle": room_title,
                # Add other top-level state info if needed by frontend
                "difficulty": game_state.difficulty,
                "roomsCleared": game_state.rooms_cleared,
            }
        except Exception as e:
            logger.exception(
                f"Error mapping game state {game_state.id} to frontend structure: {e}"
            )
            return None

    def _map_player_to_schema(self, player: Player) -> PlayerStatsSchema:
        """Maps the Player model to the PlayerStatsSchema."""
        # Example XP calculation (adjust as needed per game design)
        max_xp = 100 * (2 ** (player.level - 1)) if player.level > 0 else 100

        try:
            return PlayerStatsSchema(
                currentHp=player.health,
                maxHp=player.max_health,
                gold=player.gold,
                xp=player.experience,
                maxXp=max_xp,
                level=player.level,
            )
        except Exception as e:
            logger.error(
                f"Error mapping player {player.id} data to PlayerStatsSchema: {e}",
                exc_info=True,
            )
            # Return a default schema on error to prevent crashing caller
            return PlayerStatsSchema(
                currentHp=0, maxHp=100, gold=0, xp=0, maxXp=100, level=1
            )

    def _map_inventory_to_schema(
        self, inventory_items: List[PlayerInventoryItem]
    ) -> List[ItemSchema]:
        """Maps PlayerInventoryItem relationship data to a list of ItemSchema."""
        items_schema_list = []
        if not inventory_items:
            return []

        for inv_item in inventory_items:
            item_model = inv_item.item  # Access the related Item model
            if not item_model:
                logger.warning(
                    f"PlayerInventoryItem (Player: {inv_item.player_id}, Qty: {inv_item.quantity}) is missing related Item data."
                )
                continue

            try:
                # Extract properties, providing defaults if None/missing
                item_props = item_model.properties or {}

                item_schema = ItemSchema(
                    # Use a combination of player/item IDs or a dedicated UUID if items needed unique instance IDs
                    id=f"item_{item_model.id}",  # Use base Item ID for now
                    name=item_model.name,
                    description=item_model.description or "",
                    quantity=inv_item.quantity,  # Get quantity from the association object
                    rarity=item_props.get("rarity", "common"),
                    icon=item_props.get("icon"),
                    canUse=item_props.get("canUse", item_props.get("usable", False)),
                    canEquip=item_props.get(
                        "canEquip", item_props.get("equipable", False)
                    ),
                    canDrop=item_props.get("canDrop", True),  # Default to droppable
                    # Add other mapped properties as needed
                )
                items_schema_list.append(item_schema)
            except Exception as e:
                logger.error(
                    f"Error mapping inventory item (Item ID: {item_model.id}, Player: {inv_item.player_id}) to ItemSchema: {e}",
                    exc_info=True,
                )
                # Optionally skip the item or add a placeholder error item

        return items_schema_list
