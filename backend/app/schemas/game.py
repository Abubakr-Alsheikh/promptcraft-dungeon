# backend/app/schemas/game.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# --- Pydantic Schemas for API Request/Response Validation ---


class ItemSchema(BaseModel):
    id: str
    name: str
    description: str
    quantity: int
    rarity: str = "common"  # Default value
    icon: Optional[str] = None
    canUse: Optional[bool] = False
    canEquip: Optional[bool] = False
    canDrop: Optional[bool] = True  # Default canDrop to True

    model_config = {
        "extra": "ignore"  # Tolerate extra fields if they come from DB JSON
    }


class PlayerStatsSchema(BaseModel):
    currentHp: int
    maxHp: int
    gold: int
    xp: int = 0  # Default XP to 0
    maxXp: int = 100  # Default maxXp
    level: int = 1  # Default level

    model_config = {"extra": "ignore"}


# Represents the core GameState needed by the frontend (subset of backend model)
class GameStateSchema(BaseModel):
    playerStats: PlayerStatsSchema
    inventory: List[ItemSchema]
    description: str  # The current room/situation description (persistent)
    roomTitle: Optional[str] = None  # Add the title of the current room/area

    model_config = {"extra": "ignore"}


# ---- Request Schemas ----


class StartGameRequest(BaseModel):
    playerName: Optional[str] = Field("Adventurer", max_length=50)
    difficulty: Optional[str] = Field("medium", pattern="^(easy|medium|hard)$")


class CommandRequest(BaseModel):
    command: str = Field(..., min_length=1)
    game_id: int = Field(..., gt=0)


# ---- Response Schemas ----


# Base for state responses (GET /state, POST /start)
class BaseStateResponse(GameStateSchema):
    game_id: int
    message: str  # Context-specific message (e.g., "Game started", "State retrieved")


# Matches frontend InitialStateResponse expectation after STARTING a game
class InitialStateResponse(BaseStateResponse):
    message: str = "Game started successfully."  # Override message default


# Matches frontend CommandResponse
class CommandResponse(BaseModel):
    success: bool
    message: str = Field(
        ...,
        description="Narrative result of the player's last action (from AI's action_result_description).",
    )
    description: str = Field(
        ...,
        description="Current description of the player's location (persistent room description).",
    )
    playerStats: PlayerStatsSchema  # Updated player stats
    updatedInventory: List[ItemSchema]  # Full updated inventory list
    roomTitle: Optional[str] = Field(
        None, description="The title of the current room/location."
    )
    soundEffect: Optional[str] = None
    game_id: int

    model_config = {"extra": "ignore"}


# Schema for GET /state/<id> response
class GetStateResponse(BaseStateResponse):
    message: str = "Current game state retrieved."  # Override message default
