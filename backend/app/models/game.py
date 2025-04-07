import json
import datetime
from typing import List, Dict, Optional, Any
from flask import current_app
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import (
    ForeignKey,
    Text,
    String,
    Integer,
    DateTime,
    JSON,
)

from ..extensions import db


# --- Item Definition ---
# Represents a type of item that can exist in the game.
# This could later be expanded into a more complex item template system.
class Item(db.Model):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(primary_key=True)
    # Unique identifier string (e.g., 'health_potion', 'rusty_sword')
    item_key: Mapped[str] = mapped_column(
        String(80), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # Display name
    description: Mapped[str] = mapped_column(Text, nullable=True, default="")
    # Store properties like usable, equippable, rarity, icon etc. as JSON?
    properties: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationship back to inventory entries (one item type can be in many players' inventories)
    inventory_entries: Mapped[List["PlayerInventoryItem"]] = relationship(
        back_populates="item"
    )

    def __repr__(self):
        return f"<Item {self.item_key} ({self.name})>"


# --- Player Inventory Association ---
# Links Players to Items and stores the quantity.
class PlayerInventoryItem(db.Model):
    __tablename__ = "player_inventory"
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Relationships to Player and Item
    player: Mapped["Player"] = relationship(back_populates="inventory_items")
    item: Mapped["Item"] = relationship(back_populates="inventory_entries")

    def __repr__(self):
        return f"<PlayerInventoryItem player_id={self.player_id} item_id={self.item_id} qty={self.quantity}>"


# --- Player Model ---
# Represents the player character.
class Player(db.Model):
    __tablename__ = "players"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False, default="Adventurer")
    health: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    max_health: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    experience: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    gold: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Link to the GameState this player belongs to
    game_state_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("game_states.id"), nullable=True
    )

    # Relationship to inventory items (replaces inventory_json)
    # cascade="all, delete-orphan": If player is deleted, their inventory entries are also deleted.
    inventory_items: Mapped[List["PlayerInventoryItem"]] = relationship(
        back_populates="player", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Player id={self.id} name={self.name} game={self.game_state_id}>"


# --- Chat Message Log ---
# Stores the history of interactions within a game session.
class ChatMessage(db.Model):
    __tablename__ = "chat_messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    game_state_id: Mapped[int] = mapped_column(
        ForeignKey("game_states.id"), nullable=False, index=True
    )
    turn_number: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # To maintain order reliably
    role: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'system', 'user', 'assistant'
    # Content can be simple text (user) or potentially JSON string (assistant AI response)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )

    # Relationship back to the GameState
    game_state: Mapped["GameState"] = relationship(back_populates="chat_messages")

    def __repr__(self):
        return f"<ChatMessage id={self.id} game={self.game_state_id} turn={self.turn_number} role={self.role}>"


# --- Game State Model ---
# Represents the overall state of a single game session.
class GameState(db.Model):
    __tablename__ = "game_states"
    id: Mapped[int] = mapped_column(primary_key=True)
    difficulty: Mapped[str] = mapped_column(
        String(50), nullable=False, default="medium"
    )
    rooms_cleared: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Store current room details as JSON. This is a compromise:
    # Easier for AI to dynamically define rooms, but harder to query room specifics.
    # If room structure becomes stable or needs querying, create a Room model.
    current_room_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Link to the Player associated with this game state
    # cascade: If GameState is deleted, the associated Player is also deleted.
    # uselist=False: One-to-one relationship (a GameState has one Player)
    player: Mapped["Player"] = relationship(
        backref=db.backref(
            "game_state", uselist=False
        ),  # Simple backref for Player -> GameState access
        cascade="all, delete-orphan",
    )

    # Relationship to chat history messages (replaces chat_history_json)
    # cascade: If GameState is deleted, its ChatMessages are also deleted.
    # order_by: Ensures messages are loaded in the correct order.
    chat_messages: Mapped[List["ChatMessage"]] = relationship(
        back_populates="game_state",
        cascade="all, delete-orphan",
        order_by="ChatMessage.turn_number",  # Order messages by turn number
    )

    # Timestamps for tracking game creation and updates
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    # --- Helper property for accessing current_room as dict ---
    @property
    def current_room(self) -> Optional[Dict[str, Any]]:
        """Load current room from JSON."""
        if self.current_room_json:
            try:
                return json.loads(self.current_room_json)
            except json.JSONDecodeError:
                # Log this error
                current_app.logger.error(
                    f"Failed to decode current_room_json for game {self.id}"
                )
                return None  # Or return a default error room structure
        return None

    @current_room.setter
    def current_room(self, value: Optional[Dict[str, Any]]):
        """Save current room as JSON."""
        if value is None:
            self.current_room_json = None
        else:
            try:
                self.current_room_json = json.dumps(value)
            except TypeError as e:
                # Log this error
                current_app.logger.error(
                    f"Failed to serialize current_room to JSON for game {self.id}: {e}"
                )
                self.current_room_json = None  # Avoid saving invalid data

    def get_chat_history_for_ai(self) -> List[Dict[str, str]]:
        """Formats the stored chat messages for the AI service."""
        history = []
        for msg in self.chat_messages:
            content = msg.content
            history.append({"role": msg.role, "content": content})
        return history

    def add_chat_message(self, role: str, content: str, turn_number: int):
        """Adds a new message to the chat history."""
        new_message = ChatMessage(
            game_state_id=self.id,
            role=role,
            content=content,
            turn_number=turn_number,
        )
        # Appending to the relationship list automatically handles the session add
        self.chat_messages.append(new_message)

    def __repr__(self):
        player_name = self.player.name if self.player else "No Player"
        return f"<GameState id={self.id} player={player_name} difficulty={self.difficulty}>"
