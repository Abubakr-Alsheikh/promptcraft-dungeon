from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
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


class GameState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player = db.relationship(
        "Player", backref="game_state", uselist=False, cascade="all, delete-orphan"
    )
    difficulty = db.Column(db.String(50), nullable=False, default="medium")
    current_room_json = db.Column(db.Text, nullable=True)  # Store current room as JSON
    rooms_cleared = db.Column(db.Integer, nullable=False, default=0)
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
