import json
import requests
import logging
from typing import Dict, Any, Optional
from flask import current_app  # Use current_app to access config
from openai import OpenAI, APITimeoutError, APIConnectionError, RateLimitError

from ..prompts.game_prompts import BASE_SYSTEM_PROMPT, INITIAL_ROOM_PROMPT_USER
from ..models.ai_responses import AIResponse  # Pydantic model for parsing

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.use_local = current_app.config["USE_LOCAL"]
        self.local_url = current_app.config["OLLAMA_URL"]
        self.gemini_api_key = current_app.config["GEMINI_API_KEY"]
        self.ollama_model = current_app.config["OLLAMA_MODEL"]
        self.gemini_model = current_app.config["GEMINI_MODEL"]
        self.timeout = current_app.config["AI_REQUEST_TIMEOUT"]

        self.gemini_client = None
        if self.gemini_api_key:
            try:
                # Using the official Google client is generally recommended now
                # Or stick with OpenAI compatible endpoint if preferred
                self.gemini_client = OpenAI(
                    api_key=self.gemini_api_key,
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",  # Adjust if using specific version/proxy
                )
                logger.info("Gemini client configured via OpenAI compatibility.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                # Proceed without Gemini if initialization fails

        # Check local availability on startup or first use?
        # Checking here might delay startup if Ollama is slow/down.
        # Deferring the check until the first call might be better UX.
        self._local_checked = False
        self._local_available = False
        if self.use_local:
            self._check_local_ollama()  # Check availability if configured to use local

    def _check_local_ollama(self):
        """Checks if the configured local Ollama instance is responsive."""
        if not current_app.config["USE_LOCAL"] or not self.local_url:
            self._local_available = False
            self._local_checked = True
            return False

        if self._local_checked:  # Don't check repeatedly if already determined
            return self._local_available

        logger.debug(f"Checking Ollama availability at {self.local_url}")
        try:
            # Use a simple endpoint like /api/tags or just /
            response = requests.get(f"{self.local_url}/", timeout=5)
            response.raise_for_status()  # Check for HTTP errors
            # Optionally, check if the desired model exists via /api/tags
            self._local_available = True
            logger.info(
                f"Local Ollama instance detected and responsive at {self.local_url}"
            )
        except requests.RequestException as e:
            self._local_available = False
            logger.warning(
                f"Local Ollama instance not available at {self.local_url}: {e}"
            )
        finally:
            self._local_checked = True  # Mark as checked

        return self._local_available

    def _format_prompt(
        self, system_template: str, user_prompt: str, context: Dict[str, Any]
    ) -> tuple[str, str]:
        """Formats the system and user prompts with dynamic context."""
        formatted_system = system_template.format(**context)
        formatted_user = user_prompt.format(**context)
        return formatted_system, formatted_user

    def generate_structured_response(
        self, system_prompt_template: str, user_prompt: str, context: Dict[str, Any]
    ) -> Optional[AIResponse]:
        """
        Generates a response from the LLM, attempts to parse it into the AIResponse model.
        Handles fallback between local and Gemini.
        """
        system_prompt, user_prompt_formatted = self._format_prompt(
            system_prompt_template, user_prompt, context
        )
        logger.debug(f"Formatted System Prompt Snippet: {system_prompt[:200]}...")
        logger.debug(f"Formatted User Prompt: {user_prompt_formatted}")

        raw_response_str = None
        use_local_for_this_call = (
            self.use_local and self._check_local_ollama()
        )  # Re-check ensures it's currently up

        if use_local_for_this_call:
            logger.info(f"Attempting query to local Ollama model: {self.ollama_model}")
            try:
                raw_response_str = self._query_local(
                    system_prompt, user_prompt_formatted
                )
            except Exception as e:
                logger.error(f"Local Ollama query failed: {e}. Falling back to Gemini.")
                use_local_for_this_call = False  # Ensure fallback happens

        # Fallback to Gemini if local failed or wasn't selected/available
        if not use_local_for_this_call:
            if self.gemini_client:
                logger.info(f"Attempting query to Gemini model: {self.gemini_model}")
                try:
                    raw_response_str = self._query_gemini(
                        system_prompt, user_prompt_formatted
                    )
                except Exception as e:
                    logger.error(f"Gemini query failed: {e}")
                    # No further fallback, error out
                    return None
            else:
                logger.error(
                    "No AI service available (Local failed/disabled, Gemini unavailable/unconfigured)."
                )
                return None

        if not raw_response_str:
            logger.error("Received empty response from AI service.")
            return None

        # --- Response Parsing ---
        try:
            # Clean potential markdown code blocks ```json ... ```
            if raw_response_str.strip().startswith("```json"):
                raw_response_str = raw_response_str.strip()[7:-3].strip()
            elif raw_response_str.strip().startswith("```"):
                raw_response_str = raw_response_str.strip()[3:-3].strip()

            response_data = json.loads(raw_response_str)
            # Validate and parse using Pydantic
            ai_response_obj = AIResponse.model_validate(response_data)
            logger.debug(
                f"Successfully parsed AI response: {ai_response_obj.model_dump_json(indent=2)}"
            )
            return ai_response_obj
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to decode AI JSON response: {e}\nRaw response:\n{raw_response_str}"
            )
            return None
        except Exception as e:  # Catch Pydantic validation errors or others
            logger.error(
                f"Failed to validate AI response against Pydantic model: {e}\nRaw response:\n{raw_response_str}"
            )
            return None

    def _query_local(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Sends request to local Ollama instance."""
        payload = {
            "model": self.ollama_model,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "format": "json",
        }
        try:
            response = requests.post(
                f"{self.local_url}/api/generate", json=payload, timeout=self.timeout
            )
            response.raise_for_status()
            # Ollama's non-streaming JSON response structure
            response_json = response.json()
            if "response" in response_json:
                logger.debug(
                    f"Raw local AI response received (length: {len(response_json['response'])})"
                )
                return response_json["response"]  # This should be the JSON string
            else:
                logger.error(
                    f"Unexpected response structure from local Ollama: {response_json}"
                )
                return None
        except requests.Timeout:
            logger.error(
                f"Local Ollama request timed out after {self.timeout} seconds."
            )
            raise TimeoutError("Local LLM request timed out")
        except requests.RequestException as e:
            logger.error(f"Local Ollama request failed: {e}")
            raise ConnectionError(f"Failed to connect to local LLM: {e}")

    def _query_gemini(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Sends request to Gemini via OpenAI compatible endpoint."""
        if not self.gemini_client:
            raise ConnectionError("Gemini client not initialized.")
        try:
            # Using Chat Completions endpoint
            response = self.gemini_client.chat.completions.create(
                model=self.gemini_model,  # Use the specific model name from config
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            result = response.choices[0].message.content
            logger.debug(f"Raw Gemini AI response received (length: {len(result)})")
            return result
        except APITimeoutError:
            logger.error(f"Gemini request timed out after {self.timeout} seconds.")
            raise TimeoutError("Gemini request timed out")
        except APIConnectionError as e:
            logger.error(f"Gemini connection error: {e}")
            raise ConnectionError(f"Failed to connect to Gemini: {e}")
        except RateLimitError as e:
            logger.error(f"Gemini rate limit exceeded: {e}")
            raise ConnectionError(
                f"Gemini rate limit exceeded: {e}"
            )  # Treat as connection issue for retry logic if any
        except Exception as e:
            logger.error(f"Gemini API request failed: {e}")
            raise RuntimeError(f"Gemini API error: {e}")

    # Methods to force switch if needed (useful for debugging/admin)
    def switch_to_local(self) -> bool:
        """Force preference to local LLM and check availability."""
        current_app.config["USE_LOCAL"] = (
            True  # Update runtime config? Be careful with this approach
        )
        self.use_local = True
        self._local_checked = False  # Force re-check on next call
        return self._check_local_ollama()

    def switch_to_gemini(self) -> bool:
        """Force preference to Gemini."""
        current_app.config["USE_LOCAL"] = False
        self.use_local = False
        return bool(self.gemini_client)  # Available if client is initialized
