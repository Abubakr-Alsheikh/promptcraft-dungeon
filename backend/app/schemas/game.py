from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any

# --- Pydantic Schemas for API Request/Response Data Structures ---
# These models define the expected structure and validation rules for data
# exchanged between the frontend and backend API endpoints.

# --- Core Data Schemas (used within other schemas) ---


class ItemSchema(BaseModel):
    """Represents a single item or stack of items in the player's inventory (frontend view)."""

    # Note: `id` is a string potentially derived from the backend item ID,
    # suitable for use as unique keys in frontend lists (e.g., React).
    id: str = Field(
        ...,
        description="Unique identifier for the item instance/stack in the frontend.",
    )
    name: str = Field(..., description="Display name of the item.")
    description: str = Field(..., description="Description of the item.")
    quantity: int = Field(..., gt=0, description="Number of items in this stack.")
    rarity: str = Field(
        "common", description="Item rarity (e.g., common, uncommon, rare)."
    )
    icon: Optional[str] = Field(None, description="Identifier/URL for the item's icon.")
    canUse: Optional[bool] = Field(
        False, description="Whether the item has a 'use' action."
    )
    canEquip: Optional[bool] = Field(
        False, description="Whether the item can be equipped."
    )
    canDrop: Optional[bool] = Field(
        True, description="Whether the item can be dropped."
    )

    model_config = ConfigDict(
        extra="ignore",  # Allow extra fields from backend models without error
        frozen=False,  # Allow modification if needed (though usually treated as immutable)
    )


class PlayerStatsSchema(BaseModel):
    """Represents the player's core statistics."""

    currentHp: int = Field(..., description="Player's current health points.")
    maxHp: int = Field(..., description="Player's maximum health points.")
    gold: int = Field(..., ge=0, description="Amount of gold the player possesses.")
    xp: int = Field(0, ge=0, description="Player's current experience points.")
    maxXp: int = Field(
        100, gt=0, description="Experience points needed for the next level."
    )
    level: int = Field(1, ge=1, description="Player's current level.")

    model_config = ConfigDict(extra="ignore")


class GameStateSchema(BaseModel):
    """Represents the core game state information needed by the frontend view."""

    playerStats: PlayerStatsSchema = Field(
        ..., description="Current player statistics."
    )
    inventory: List[ItemSchema] = Field(
        ..., description="List of items in the player's inventory."
    )
    description: str = Field(
        ...,
        description="The persistent description of the player's current location or situation.",
    )
    roomTitle: Optional[str] = Field(
        None, description="The title or name of the current room/area."
    )

    model_config = ConfigDict(extra="ignore")


# ---- Request Schemas ----


class StartGameRequest(BaseModel):
    """Schema for the request body of the POST /api/game/start endpoint."""

    playerName: Optional[str] = Field(
        default="Adventurer",
        max_length=50,
        description="Optional name for the player character.",
    )
    difficulty: Optional[str] = Field(
        default="medium",
        pattern=r"^(easy|medium|hard)$",  # Regex pattern for validation
        description="Game difficulty setting ('easy', 'medium', or 'hard').",
    )
    model_config = ConfigDict(extra="forbid")  # Forbid extra fields in requests


class CommandRequest(BaseModel):
    """Schema for the request body of the POST /api/game/command endpoint."""

    command: str = Field(
        ...,
        min_length=1,
        max_length=200,  # Add a reasonable max length
        description="The command input by the player.",
    )
    game_id: int = Field(
        ..., gt=0, description="The unique identifier of the game session."
    )
    model_config = ConfigDict(extra="forbid")


# ---- Response Schemas ----


class ErrorResponse(BaseModel):
    """Standardized structure for API error responses."""

    error: str = Field(
        ...,
        description="A short code or title for the error (e.g., 'Not Found', 'Validation Error').",
    )
    message: str = Field(
        ..., description="A human-readable message explaining the error."
    )
    details: Optional[Any] = Field(
        None,
        description="Optional field for additional error details (e.g., validation errors).",
    )

    model_config = ConfigDict(extra="ignore")


class BaseStateResponse(GameStateSchema):
    """Base structure for responses that include the core game state view."""

    game_id: int = Field(..., description="The unique identifier of the game session.")
    message: str = Field(
        ..., description="A context-specific status message related to the response."
    )


class InitialStateResponse(BaseStateResponse):
    """Response schema for successfully starting a new game (POST /api/game/start)."""

    message: str = Field(
        "Game started successfully.", description="Confirmation message for game start."
    )
    # soundEffect is typically not needed on initial start, but could be added if desired
    soundEffect: Optional[str] = Field(
        None, description="Optional sound effect suggestion for game start."
    )

    model_config = ConfigDict(extra="ignore")  # Allow other BaseStateResponse fields


class CommandResponse(BaseModel):
    """Response schema for successfully processing a player command (POST /api/game/command)."""

    success: bool = Field(
        ...,
        description="Indicates if the command was processed successfully (should always be true here, errors use ErrorResponse).",
    )
    message: str = Field(
        ...,
        description="Narrative result of the player's last action (from AI's action_result_description).",
    )
    description: str = Field(
        ..., description="Current persistent description of the player's location."
    )
    playerStats: PlayerStatsSchema = Field(
        ..., description="Updated player statistics after the command."
    )
    # Renamed for clarity vs. GameStateSchema.inventory
    updatedInventory: List[ItemSchema] = Field(
        ..., description="The complete, updated inventory list after the command."
    )
    roomTitle: Optional[str] = Field(
        None, description="The title of the current room/location after the command."
    )
    soundEffect: Optional[str] = Field(
        None, description="Sound effect suggested by the AI for this action's result."
    )
    game_id: int = Field(..., description="The unique identifier of the game session.")
    # Include other state parts if needed by frontend after a command
    difficulty: Optional[str] = Field(None, description="Current game difficulty.")
    roomsCleared: Optional[int] = Field(
        None, description="Number of rooms/areas cleared."
    )

    model_config = ConfigDict(extra="ignore")


class GetStateResponse(BaseStateResponse):
    """Response schema for retrieving the current game state (GET /api/game/state/{id})."""

    message: str = Field(
        "Current game state retrieved.",
        description="Confirmation message for state retrieval.",
    )
    # soundEffect usually not applicable for just getting state
    soundEffect: Optional[str] = Field(
        None, description="Optional sound effect suggestion (usually None here)."
    )

    model_config = ConfigDict(extra="ignore")  # Allow other BaseStateResponse fields
