from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any

# --- Pydantic Models for Structured AI Output ---
# These models define the expected JSON structure that the AI service (Ollama/Gemini)
# should return. This allows for reliable parsing and validation of the AI's response.


class AIEventEffect(BaseModel):
    """
    Represents the specific, quantifiable effects of an AI-generated event
    on the player's state or inventory.
    """

    health: Optional[str] = Field(
        None,
        description="Player health change, e.g., '-10', '+5'. Must be parseable as int.",
    )
    inventory_add: List[str] = Field(
        default_factory=list,
        description="List of specific item names to be added to player inventory.",
    )
    inventory_remove: List[str] = Field(
        default_factory=list,
        description="List of specific item names to be removed from player inventory.",
    )
    gold: Optional[str] = Field(
        None,
        description="Player gold change, e.g., '+50', '-10'. Must be parseable as int.",
    )
    xp: Optional[str] = Field(
        None,
        description="Player experience points change, e.g., '+25'. Must be parseable as int.",
    )
    status_effect_add: List[str] = Field(
        default_factory=list,
        description="Status effects to add, e.g., ['poisoned', 'blinded'].",
    )
    status_effect_remove: List[str] = Field(
        default_factory=list,
        description="Status effects to remove, e.g., ['poisoned'].",
    )
    # Add other potential effects like mana, temporary stat changes, etc. if needed

    model_config = ConfigDict(extra="ignore")  # Ignore unexpected fields from AI


class AIEvent(BaseModel):
    """
    Represents a distinct event triggered by a player action or occurring spontaneously,
    as determined by the AI.
    """

    type: str = Field(
        ...,
        description="Categorizes the event, e.g., 'combat', 'treasure', 'trap', 'puzzle', 'narration', 'status_change', 'environment', 'dialogue', 'move'.",
    )
    description: str = Field(
        ..., description="Narrative description of the event itself."
    )
    resolution: Optional[str] = Field(
        None,
        description="Optional text describing the immediate outcome or resolution of the event, if applicable (e.g., 'The goblin is defeated', 'The lock clicks open').",
    )
    effects: Optional[AIEventEffect] = Field(
        None, description="Specific effects this event has on the game state."
    )

    model_config = ConfigDict(extra="ignore")


class AIResponse(BaseModel):
    """
    Represents the complete, structured response expected from the AI Narrator
    after processing a player command and the current game context.
    """

    action_result_description: str = Field(
        ...,
        description="Narrative text describing the immediate outcome of the player's action. Should be concise and focus on the direct result of the command.",
    )
    triggered_events: Optional[List[AIEvent]] = Field(
        default_factory=list,
        description="A list of significant events that occurred as a consequence of the player's action (e.g., combat hits, finding items, triggering traps, status changes). Minor details should be part of action_result_description.",
    )
    room_description: Optional[str] = Field(
        None,
        description="Full atmospheric description of a NEW distinct area/room the player has just entered *because* of their action. MUST be null or omitted if the player remains in the same general location.",
    )
    new_room_title: Optional[str] = Field(
        None,
        description="Suggested title for the new room, only if 'room_description' is provided.",
    )
    suggested_actions: Optional[List[str]] = Field(
        None,
        description="List of 3-5 suggested next actions based on the current situation (e.g., ['Examine the altar', 'Search the chest', 'Go north']). Should be short, actionable phrases. Provide only if relevant actions are apparent.",
    )
    sound_effect: Optional[str] = Field(
        None,
        description="Suggest ONE simple, relevant sound effect key for the frontend (e.g., 'sword_hit', 'door_creak', 'potion_drink', 'footsteps_stone', 'monster_growl', 'item_pickup'). Should be from a predefined list if possible.",
    )

    # Pydantic v2 configuration using model_config
    model_config = ConfigDict(
        extra="ignore",  # Ignore extra fields from AI instead of raising validation error
        validate_assignment=True,  # Validate fields when assigned after initialization
    )
