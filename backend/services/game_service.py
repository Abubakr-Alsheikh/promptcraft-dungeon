from models import GameState, Player


class GameService:
    @staticmethod
    def process_action(game_state: GameState, action: dict) -> GameState:
        """Process player action and update game state"""
        action_type = action.get("type")

        if action_type == "move":
            return GameService._handle_movement(game_state, action)
        elif action_type == "attack":
            return GameService._handle_combat(game_state, action)
        elif action_type == "use":
            return GameService._handle_item_use(game_state, action)
        else:
            raise ValueError("Invalid action type")

    @staticmethod
    def _handle_movement(game_state: GameState, action: dict) -> GameState:
        # Update game state for movement
        game_state.rooms_cleared += 1
        return game_state

    @staticmethod
    def _handle_combat(game_state: GameState, action: dict) -> GameState:
        # Simplified combat logic
        enemy_damage = {"easy": 5, "medium": 10, "hard": 15}.get(
            game_state.difficulty, 10
        )

        game_state.player.health -= enemy_damage
        return game_state

    @staticmethod
    def _handle_item_use(game_state: GameState, action: dict) -> GameState:
        item = action.get("item")
        if item in game_state.player.inventory:
            game_state.player.inventory.remove(item)
            if item == "healing_potion":
                game_state.player.health = min(100, game_state.player.health + 30)
        return game_state
