import json
import requests
from prompts import SYSTEM_PROMPT
from config import Config


class AIService:
    @staticmethod
    def generate_initial_room(game_state):
        prompt = f"""
        Generate the initial dungeon room for a {game_state.difficulty} difficulty level.
        Theme: ancient ruins
        Player: {game_state.player.name}
        """
        return AIService._query_llm(prompt, system_prompt=SYSTEM_PROMPT)

    @staticmethod
    def generate_response(game_state, action):
        prompt = f"""
        Current room: {game_state.current_room.description}
        Player action: {action}
        Player status: Health {game_state.player.health}, Inventory {game_state.player.inventory}
        """
        return AIService._query_llm(prompt, system_prompt=SYSTEM_PROMPT)

    @staticmethod
    def _query_llm(prompt, system_prompt):
        try:
            payload = {
                "model": "deepseek-r1:1.5B",
                "system": system_prompt,
                "prompt": prompt,
                "stream": False,
            }

            response = requests.post(
                f"{Config.OLLAMA_URL}/api/generate", json=payload, timeout=30
            )
            response.raise_for_status()
            raw_response = AIService._parse_response(response.text)["response"]
            print(f"Raw AI response: {raw_response}")
            return raw_response

        except Exception as e:
            raise RuntimeError(f"AI service error: {str(e)}")

    @staticmethod
    def _parse_response(raw_response):
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError:
            return {"error": "Failed to parse AI response"}
