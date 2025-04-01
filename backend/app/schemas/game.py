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
    # Frontend MUST send the game_id for subsequent commands
    game_id: int = Field(..., gt=0)  # Add game_id, ensure it's positive


# ---- Response Schemas ----


# Matches frontend InitialStateResponse expectation after STARTING a game
class InitialStateResponse(GameStateSchema):
    # Inherits fields from GameStateSchema
    game_id: int  # Crucial: Backend sends the ID of the created game state
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
    game_id: int  # Also return game_id in command response for consistency/verification


# Optional: Schema for getting state directly (if used)
class GetStateResponse(GameStateSchema):
    game_id: int
    message: Optional[str] = None
