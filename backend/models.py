from dataclasses import dataclass, asdict
from typing import List, Dict


@dataclass
class Player:
    name: str
    health: int = 100
    inventory: List[str] = None
    experience: int = 0

    def __post_init__(self):
        self.inventory = self.inventory or []

    def to_dict(self):
        return asdict(self)


@dataclass
class GameState:
    player: Player
    difficulty: str = "medium"
    current_room: Dict = None
    rooms_cleared: int = 0

    def to_dict(self):
        return {
            "player": self.player.to_dict(),
            "difficulty": self.difficulty,
            "current_room": self.current_room,
            "rooms_cleared": self.rooms_cleared,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            player=Player(**data["player"]),
            difficulty=data["difficulty"],
            current_room=data.get("current_room"),
            rooms_cleared=data.get("rooms_cleared", 0),
        )
