from dataclasses import dataclass, field, asdict
import json
from typing import List, Dict, Optional, Any, TypedDict

from flask import current_app
from ..extensions import db  # Import db instance

# --- Core Data Models (Consider using SQLAlchemy for DB persistence) ---


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, default="Adventurer")
    health = db.Column(db.Integer, nullable=False, default=100)
    max_health = db.Column(db.Integer, nullable=False, default=100)
    inventory_json = db.Column(db.Text, nullable=True)  # Store inventory as JSON string
    experience = db.Column(db.Integer, nullable=False, default=0)
    level = db.Column(db.Integer, nullable=False, default=1)
    gold = db.Column(db.Integer, nullable=False, default=0)
    game_state_id = db.Column(
        db.Integer, db.ForeignKey("game_state.id"), nullable=True
    )  # Link to GameState

    @property
    def inventory(self) -> List[Dict[str, Any]]:
        """Load inventory from JSON."""
        if self.inventory_json:
            import json

            try:
                return json.loads(self.inventory_json)
            except json.JSONDecodeError:
                return []
        return []

    @inventory.setter
    def inventory(self, value: List[Dict[str, Any]]):
        """Save inventory as JSON."""
        import json

        self.inventory_json = json.dumps(value)

    def to_dict(self) -> Dict[str, Any]:
        """Convert Player model to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "currentHp": self.health,
            "maxHp": self.max_health,
            "inventory": self.inventory,
            "xp": self.experience,
            # maxXp calculation might depend on level, add logic if needed
            "maxXp": 100 * self.level,  # Example calculation
            "level": self.level,
            "gold": self.gold,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create Player instance from dictionary (useful for initial creation)."""
        player = cls(
            name=data.get("name", "Adventurer"),
            health=data.get("currentHp", 100),
            max_health=data.get("maxHp", 100),
            experience=data.get("xp", 0),
            level=data.get("level", 1),
            gold=data.get("gold", 0),
        )
        player.inventory = data.get("inventory", [])  # Use the setter
        return player


class ChatMessage(TypedDict):
    role: str  # 'system', 'user', 'assistant'
    content: str


class GameState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player = db.relationship(
        "Player", backref="game_state", uselist=False, cascade="all, delete-orphan"
    )
    difficulty = db.Column(db.String(50), nullable=False, default="medium")
    current_room_json = db.Column(db.Text, nullable=True)  # Store current room as JSON
    rooms_cleared = db.Column(db.Integer, nullable=False, default=0)
    chat_history_json = db.Column(db.Text, nullable=True)
    # Add session ID or user ID if implementing multi-user persistence
    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    @property
    def current_room(self) -> Optional[Dict[str, Any]]:
        """Load current room from JSON."""
        if self.current_room_json:
            import json

            try:
                return json.loads(self.current_room_json)
            except json.JSONDecodeError:
                return None
        return None

    @current_room.setter
    def current_room(self, value: Optional[Dict[str, Any]]):
        """Save current room as JSON."""
        import json

        if value is None:
            self.current_room_json = None
        else:
            self.current_room_json = json.dumps(value)

    @property
    def chat_history(
        self,
    ) -> List[Dict[str, str]]:  # Use Dict for simplicity or ChatMessage
        """Load chat history from JSON."""
        if self.chat_history_json:
            try:
                history = json.loads(self.chat_history_json)
                # Basic validation: ensure it's a list of dicts with 'role' and 'content'
                if isinstance(history, list) and all(
                    isinstance(msg, dict) and "role" in msg and "content" in msg
                    for msg in history
                ):
                    return history
                else:
                    # Log error or return default if structure is invalid
                    current_app.logger.warning(
                        f"Invalid chat history JSON structure for game {self.id}. Resetting."
                    )
                    return []
            except json.JSONDecodeError:
                current_app.logger.error(
                    f"Failed to decode chat history JSON for game {self.id}. Resetting."
                )
                return []
        return []  # Return empty list if no history stored yet

    @chat_history.setter
    def chat_history(self, value: List[Dict[str, str]]):
        """Save chat history as JSON."""
        if value is None:
            self.chat_history_json = None
        else:
            # Optional: Add validation before saving if needed
            self.chat_history_json = json.dumps(value)

    def to_dict(self) -> Dict[str, Any]:
        """Convert GameState model to dictionary."""
        return {
            "id": self.id,
            "player": self.player.to_dict() if self.player else None,
            "difficulty": self.difficulty,
            "current_room": self.current_room,
            "rooms_cleared": self.rooms_cleared,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create GameState instance from dictionary (useful for updates)."""
        state = cls(
            difficulty=data.get("difficulty", "medium"),
            rooms_cleared=data.get("rooms_cleared", 0),
        )
        state.current_room = data.get("current_room")  # Use setter
        if "player" in data:
            # This assumes player exists or needs creation based on context
            # More complex logic might be needed for finding/updating existing players
            state.player = Player.from_dict(data["player"])
        return state
