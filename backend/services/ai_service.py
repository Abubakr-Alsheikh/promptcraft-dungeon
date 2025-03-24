import json
import requests
from openai import OpenAI
from prompts import SYSTEM_PROMPT
from config import Config


class AIService:
    def __init__(self):
        # Initialize both clients
        self.use_local = self._check_local_available()
        self.local_url = Config.OLLAMA_URL
        self.gemini_api_key = Config.GEMINI_API_KEY

        # Configure OpenAI client for Gemini
        self.gemini_client = OpenAI(
            api_key=self.gemini_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )

    @staticmethod
    def _check_local_available():
        """Check if local Ollama instance is running"""
        try:
            response = requests.get(f"{Config.OLLAMA_URL}/api/tags", timeout=5)
            print(response.status_code == 200 and Config.USE_LOCAL)
            return response.status_code == 200 and Config.USE_LOCAL
        except requests.RequestException:
            return False

    def generate_initial_room(self, game_state):
        prompt = f"""
        Generate the initial dungeon room for a {game_state.difficulty} difficulty level.
        Theme: ancient ruins
        Player: {game_state.player.name}
        """
        return self._query_llm(prompt, system_prompt=SYSTEM_PROMPT)

    def generate_response(self, game_state, action):
        prompt = f"""
        Current room: {game_state.current_room.description}
        Player action: {action}
        Player status: Health {game_state.player.health}, Inventory {game_state.player.inventory}
        """
        return self._query_llm(prompt, system_prompt=SYSTEM_PROMPT)

    def _query_llm(self, prompt, system_prompt):
        """Query either local LLM or Gemini based on availability/preference"""
        if self.use_local:
            return self._query_local(prompt, system_prompt)
        return self._query_gemini(prompt, system_prompt)

    def _query_local(self, prompt, system_prompt):
        """Query local Ollama instance"""
        try:
            payload = {
                "model": "deepseek-r1:1.5B",
                "system": system_prompt,
                "prompt": prompt,
                "stream": False,
            }
            response = requests.post(
                f"{self.local_url}/api/generate", json=payload, timeout=30
            )
            response.raise_for_status()
            raw_response = self._parse_response(response.text)["response"]
            print(f"Raw local AI response: {raw_response}")
            return raw_response
        except Exception as e:
            print(f"Local AI error: {str(e)}, falling back to Gemini")
            self.use_local = False
            return self._query_gemini(prompt, system_prompt)

    def _query_gemini(self, prompt, system_prompt):
        """Query Gemini using OpenAI client"""
        try:
            response = self.gemini_client.chat.completions.create(
                model="gemini-2.0-flash",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )
            result = response.choices[0].message.content
            print(f"Gemini AI response: {result}")
            return result
        except Exception as e:
            raise RuntimeError(f"Gemini AI service error: {str(e)}")

    @staticmethod
    def _parse_response(raw_response):
        """Parse response from local LLM"""
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError:
            return {"error": "Failed to parse AI response"}

    def switch_to_local(self):
        """Force switch to local LLM"""
        self.use_local = self._check_local_available()
        return self.use_local

    def switch_to_gemini(self):
        """Force switch to Gemini"""
        self.use_local = False
        return True
