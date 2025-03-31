from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# --- Pydantic Models for Structured AI Output ---
# These should match the JSON structure defined in your SYSTEM_PROMPT


class AIEventEffect(BaseModel):
    health: Optional[str] = None  # e.g., "-10", "+5"
    inventory_add: List[str] = Field(default_factory=list)  # Items to add
    inventory_remove: List[str] = Field(default_factory=list)  # Items to remove
    gold: Optional[str] = None  # e.g. "+50", "-10"
    xp: Optional[str] = None  # e.g. "+25"
    # Add other potential effects (status effects, stat changes)


class AIEvent(BaseModel):
    type: str  # e.g., "combat", "treasure", "trap", "puzzle", "narration", "move"
    description: str  # Narrative description of the event itself
    resolution: Optional[str] = None  # Outcome text, if applicable
    effects: Optional[AIEventEffect] = None
    # Optional: Add fields for combat specifics (enemies, stats) if type is combat


class AIRoom(BaseModel):
    title: str
    description: str  # Main atmospheric description of the room/scene
    exits: List[str] = Field(
        default_factory=list
    )  # Available exits (e.g., ["north", "east"])
    events: List[AIEvent] = Field(
        default_factory=list
    )  # Events triggered by entering or action
    # Optional: Add fields like 'ambient_sound', 'lighting' etc.


class AIResponse(BaseModel):
    """
    Represents the full, structured response expected from the AI
    after processing a player command.
    """

    new_room_description: Optional[str] = None  # If moving to a new room/area
    action_result_description: (
        str  # Narrative text describing the outcome of the player's action
    )
    triggered_events: List[AIEvent] = Field(
        default_factory=list
    )  # Events that happened due to the action
    sound_effect: Optional[str] = None  # Suggest sound effect name for frontend
    player_status_update: Optional[Dict[str, Any]] = (
        None  # Explicit player stat changes (optional, could use events.effects)
    )

    # We might not need a full new AIRoom object for every action,
    # often just description updates and events are enough.
    # If the action *results* in moving to a new room, that logic
    # would trigger a separate call to generate the *next* room structure.
