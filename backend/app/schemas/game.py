from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# --- Pydantic Schemas for API Request/Response Validation ---


# Represents the structure expected in apiClient.ts Item type
class ItemSchema(BaseModel):
    id: str
    name: str
    description: str
    quantity: int
    rarity: str  # Consider Enum later: "common" | "uncommon" | "rare" | "epic" | "legendary"
    icon: Optional[str] = None
    canUse: Optional[bool] = False
    canEquip: Optional[bool] = False
    canDrop: Optional[bool] = False


# Represents the structure expected in apiClient.ts PlayerStatsData
class PlayerStatsSchema(BaseModel):
    currentHp: int
    maxHp: int
    gold: int
    xp: Optional[int] = 0
    maxXp: Optional[int] = 100  # Or calculated based on level
    level: Optional[int] = 1
    # Optional: Add status effects, mana, etc.


# Represents the core GameState needed by the frontend (subset of backend model)
class GameStateSchema(BaseModel):
    playerStats: PlayerStatsSchema
    inventory: List[ItemSchema]
    description: str  # The current room/situation description from the AI
    # Optional: Add current room details if needed beyond description (e.g., exits)
    # current_room_title: Optional[str] = None
    # available_exits: Optional[List[str]] = None


# ---- Request Schemas ----


class StartGameRequest(BaseModel):
    playerName: Optional[str] = Field("Adventurer", max_length=50)
    difficulty: Optional[str] = Field(
        "medium", pattern="^(easy|medium|hard)$"
    )  # Example validation


class CommandRequest(BaseModel):
    command: str = Field(..., min_length=1)  # Ensure command is not empty
    # We might not need to send the full game state *back* from the frontend
    # if the backend maintains it (e.g., via session or DB).
    # However, sending relevant parts can make the backend stateless per request.
    # For now, assume backend loads state based on context (e.g. session/DB id)
    # current_game_state_id: Optional[int] = None # If using DB persistence


# ---- Response Schemas ----


# Matches frontend InitialStateResponse
class InitialStateResponse(GameStateSchema):
    # Inherits fields from GameStateSchema
    # Add any other initial state specific fields if needed
    message: str = "Game started successfully."


# Matches frontend CommandResponse
class CommandResponse(BaseModel):
    success: bool
    message: (
        str  # High-level outcome message (e.g., "You moved north.", "Attack failed.")
    )
    description: str  # The *new* narrative description from the AI
    playerStats: PlayerStatsSchema  # Updated player stats
    updatedInventory: List[ItemSchema]  # Full updated inventory list
    soundEffect: Optional[str] = None  # Sound effect hint
    # Optional: Add logs if backend generates them
    # logs: List[LogEntrySchema] = []
