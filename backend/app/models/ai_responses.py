# backend/app/models/ai_responses.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# --- Pydantic Models for Structured AI Output ---


class AIEventEffect(BaseModel):
    health: Optional[str] = None  # e.g., "-10", "+5"
    inventory_add: List[str] = Field(default_factory=list)  # Items to add
    inventory_remove: List[str] = Field(default_factory=list)  # Items to remove
    gold: Optional[str] = None  # e.g. "+50", "-10"
    xp: Optional[str] = None  # e.g. "+25"
    # Add other potential effects (status effects, stat changes)
    status_effect_add: List[str] = Field(
        default_factory=list
    )  # Optional: e.g., ["poisoned", "blinded"]
    status_effect_remove: List[str] = Field(
        default_factory=list
    )  # Optional: e.g., ["poisoned"]


class AIEvent(BaseModel):
    type: str  # e.g., "combat", "treasure", "trap", "puzzle", "narration", "move", "status_change", "environment", "dialogue"
    description: str  # Narrative description of the event itself
    resolution: Optional[str] = (
        None  # Outcome text, if applicable (e.g., 'The goblin is defeated')
    )
    effects: Optional[AIEventEffect] = None
    # Optional: Add fields for combat specifics (enemies, stats) if type is combat


# AIRoom is not directly used in AIResponse but kept for potential future use/reference
# class AIRoom(BaseModel):
#     title: str
#     description: str
#     exits: List[str] = Field(default_factory=list)
#     events: List[AIEvent] = Field(default_factory=list)


class AIResponse(BaseModel):
    """
    Represents the full, structured response expected from the AI
    after processing a player command.
    """

    action_result_description: str = Field(
        ...,
        description="Narrative text describing the immediate outcome of the player's action. Should be relatively concise.",
    )
    triggered_events: List[AIEvent] = Field(
        default_factory=list,
        description="Events that happened *because* of the action (combat hits, finding items, status changes, etc.).",
    )
    # --- RENAMED FIELD ---
    room_description: Optional[str] = Field(
        None,
        description="Full atmospheric description of a NEW distinct area/room the player just entered due to their action. Omit or set to null if the player remains in the same general location.",
    )
    # Optional: AI could suggest title/exits for the new room if room_description is provided
    new_room_title: Optional[str] = Field(
        None, description="Suggested title for the new room, if applicable."
    )
    new_room_exits: Optional[List[str]] = Field(
        None, description="Suggested exits for the new room, if applicable."
    )

    sound_effect: Optional[str] = Field(
        None,
        description="Suggest ONE simple, relevant sound effect name for frontend (e.g., 'sword_hit', 'door_creak').",
    )
    # player_status_update: Optional[Dict[str, Any]] = None # Deprecated in favor of using triggered_events with effects

    model_config = {
        "extra": "ignore"  # Ignore extra fields from AI instead of erroring
    }
