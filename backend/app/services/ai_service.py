import json
import string
import requests
import logging
from typing import Dict, Any, List, Optional, Tuple
from flask import current_app
from openai import (
    OpenAI,
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
    APIStatusError,
)

from ..models.ai_responses import AIResponse  # Pydantic model for parsing

logger = logging.getLogger(__name__)


# Custom Exception for AI Service issues
class AIResponseError(Exception):
    """Custom exception for errors during AI response generation or parsing."""

    pass


class AIService:
    """
    Handles interactions with AI language models (local Ollama or cloud-based Gemini).
    Manages model selection, prompt formatting, API calls, and response parsing.
    """

    def __init__(self):
        self.use_local_preference: bool = current_app.config.get("USE_LOCAL")
        self.local_url: Optional[str] = current_app.config.get("OLLAMA_URL")
        self.gemini_api_key: Optional[str] = current_app.config.get("GEMINI_API_KEY")
        self.ollama_model: str = current_app.config.get("OLLAMA_MODEL")
        self.gemini_model: str = current_app.config.get("GEMINI_MODEL")
        self.timeout: int = current_app.config.get("AI_REQUEST_TIMEOUT")

        self.gemini_client: Optional[OpenAI] = None
        if self.gemini_api_key:
            try:
                self.gemini_client = OpenAI(
                    api_key=self.gemini_api_key,
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                )
                logger.info(f"Gemini client configured for model: {self.gemini_model}")
            except Exception as e:
                logger.error(
                    f"Failed to initialize Google AI client (via OpenAI SDK): {e}"
                )
                # Proceed without Gemini client if initialization fails

        self._local_checked: bool = False
        self._local_available: bool = False
        # Initial check only if local usage is preferred and URL is set
        if self.use_local_preference and self.local_url:
            self._check_local_ollama()

    def _check_local_ollama(self) -> bool:
        """Checks if the configured local Ollama instance is responsive."""
        if not self.local_url:
            logger.warning(
                "Ollama URL not configured, cannot check local availability."
            )
            self._local_available = False
            self._local_checked = True
            return False

        # Avoid repeated checks if status is known
        if self._local_checked:
            return self._local_available

        logger.debug(f"Checking Ollama availability at {self.local_url}")
        try:
            # Use a simple request to the base URL or a known endpoint like /api/tags
            response = requests.get(f"{self.local_url}/", timeout=5)
            response.raise_for_status()  # Check for HTTP errors 4xx/5xx

            # Check if the specific model is available via /api/tags
            tags_response = requests.get(f"{self.local_url}/api/tags", timeout=5)
            if tags_response.ok:
                models = tags_response.json().get("models", [])
                if not any(m["name"] == self.ollama_model for m in models):
                    logger.warning(
                        f"Ollama instance is up, but model '{self.ollama_model}' not found."
                    )
                    # Decide if this counts as 'unavailable' - for now, let's say instance up is enough
            else:
                logger.warning(
                    f"Could not verify model list from Ollama at {self.local_url}/api/tags"
                )

            self._local_available = True
            logger.info(
                f"Local Ollama instance detected and responsive at {self.local_url}"
            )
        except requests.Timeout:
            logger.warning(f"Timeout checking Ollama availability at {self.local_url}")
            self._local_available = False
        except requests.RequestException as e:
            self._local_available = False
            logger.warning(
                f"Local Ollama instance check failed for {self.local_url}: {e}"
            )
        finally:
            self._local_checked = True  # Mark as checked regardless of outcome

        return self._local_available

    def _format_system_prompt(self, system_template: str, context: dict) -> str:
        """Safely formats the system prompt template with available context."""
        try:
            # Use string.Formatter().vformat for safe substitution (handles missing keys)
            # However, simple format with filtered context is often sufficient if keys are known
            template_keys = {
                fname
                for _, fname, _, _ in string.Formatter().parse(system_template)
                if fname
            }
            filtered_context = {k: v for k, v in context.items() if k in template_keys}
            # Provide default values for any keys still missing in filtered_context but present in template
            # This prevents KeyErrors if context is incomplete
            for key in template_keys:
                filtered_context.setdefault(
                    key, f"<{key}_unavailable>"
                )  # Placeholder for missing info
            return system_template.format(**filtered_context)
        except Exception as e:
            logger.error(
                f"Error formatting system prompt: {e}. Using raw template.",
                exc_info=True,
            )
            return system_template  # Fallback to unformatted template

    def generate_structured_response(
        self,
        system_prompt_template: str,
        history: List[Dict[str, str]],
        user_command: str,
        context: Dict[str, Any],
    ) -> Tuple[Optional[AIResponse], Optional[str]]:
        """
        Generates a structured response from the LLM, handling model selection and parsing.

        Args:
            system_prompt_template: The template string for the system prompt.
            history: List of previous chat messages [{"role": ..., "content": ...}].
            user_command: The current user input.
            context: Dictionary with dynamic data to fill into the system prompt template.

        Returns:
            A tuple containing:
            - AIResponse object if successful, None otherwise.
            - An error message string if unsuccessful, None otherwise.
        """
        system_prompt = self._format_system_prompt(system_prompt_template, context)
        logger.debug(f"Using System Prompt (first 200 chars): {system_prompt[:200]}...")
        logger.debug(f"Current User Command: {user_command}")
        logger.debug(f"Processing with History (length): {len(history)}")

        # Construct the message list for the AI API
        messages = (
            [{"role": "system", "content": system_prompt}]
            + history
            + [{"role": "user", "content": user_command}]
        )

        raw_response_str: Optional[str] = None
        error_message: Optional[str] = None
        service_used: str = "None"

        # Determine which service to use (Local preferred and available? -> Local, else Gemini if configured)
        use_local_for_this_call = (
            self.use_local_preference
            and self.local_url
            and self._check_local_ollama()  # Re-check availability might be needed if it can go down
        )

        if use_local_for_this_call:
            service_used = f"Ollama ({self.ollama_model})"
            logger.info(f"Attempting query to {service_used}")
            try:
                raw_response_str = self._query_local(messages)
            except (ConnectionError, TimeoutError, Exception) as e:
                logger.error(
                    f"Local Ollama query failed: {e}. Trying fallback.", exc_info=True
                )
                error_message = f"Local AI ({self.ollama_model}) failed: {e}. "
                use_local_for_this_call = False  # Ensure fallback happens

        # Fallback to Gemini if local failed or wasn't preferred/available
        if not use_local_for_this_call:
            if self.gemini_client:
                service_used = f"Gemini ({self.gemini_model})"
                logger.info(f"Attempting query to {service_used}")
                try:
                    raw_response_str = self._query_gemini(messages)
                    error_message = None  # Clear previous error if Gemini succeeds
                except (ConnectionError, TimeoutError, APIStatusError, Exception) as e:
                    logger.error(f"Gemini query failed: {e}", exc_info=True)
                    # Append Gemini error to any previous local error
                    error_message = (
                        error_message or ""
                    ) + f"Cloud AI ({self.gemini_model}) failed: {e}"
                    raw_response_str = None  # Ensure no partial response is used
            else:
                # No local success and no Gemini client configured/available
                logger.error(
                    "No AI service available (Local failed/disabled, and Gemini unavailable/unconfigured)."
                )
                if not error_message:  # If local wasn't even tried
                    error_message = "No AI service is available or configured."
                return None, error_message

        # --- Parse and Validate the Response ---
        if not raw_response_str:
            logger.error(f"Received no response content from {service_used}.")
            return (
                None,
                error_message
                or f"AI service ({service_used}) returned an empty response.",
            )

        try:
            logger.debug(
                f"Raw AI response from {service_used}:\n{raw_response_str[:500]}..."
            )  # Log snippet

            # Clean potential markdown code blocks
            cleaned_response_str = raw_response_str.strip()
            if cleaned_response_str.startswith("```json"):
                cleaned_response_str = cleaned_response_str[7:]
                if cleaned_response_str.endswith("```"):
                    cleaned_response_str = cleaned_response_str[:-3]
            elif cleaned_response_str.startswith("```"):
                cleaned_response_str = cleaned_response_str[3:]
                if cleaned_response_str.endswith("```"):
                    cleaned_response_str = cleaned_response_str[:-3]
            elif cleaned_response_str.startswith("{") and cleaned_response_str.endswith(
                "}"
            ):
                # Looks like plain JSON, proceed
                pass
            else:
                # AI might have returned plain text instead of JSON
                logger.warning(
                    f"AI response from {service_used} does not appear to be JSON. Content: {cleaned_response_str[:200]}..."
                )
                # Attempt to find JSON within the string if possible
                json_start = cleaned_response_str.find("{")
                json_end = cleaned_response_str.rfind("}")
                if json_start != -1 and json_end != -1 and json_start < json_end:
                    logger.info(
                        "Attempting to extract JSON block from non-JSON response..."
                    )
                    cleaned_response_str = cleaned_response_str[
                        json_start : json_end + 1
                    ]
                else:
                    raise AIResponseError(
                        "Response was not valid JSON and no JSON block could be extracted."
                    )

            response_data = json.loads(cleaned_response_str)
            ai_response_obj = AIResponse.model_validate(
                response_data
            )  # Use Pydantic validation
            logger.debug(f"Successfully parsed AI response from {service_used}.")
            # logger.debug(f"Parsed AI response object: {ai_response_obj.model_dump_json(indent=2)}")
            return ai_response_obj, None  # Success
        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to decode AI JSON response from {service_used}: {e}",
                exc_info=True,
            )
            logger.error(f"Raw response content was:\n{raw_response_str}")
            return None, f"AI returned invalid JSON: {e}"
        except AIResponseError as e:  # Catch our custom JSON extraction error
            logger.error(
                f"Failed to process AI response from {service_used}: {e}", exc_info=True
            )
            logger.error(f"Raw response content was:\n{raw_response_str}")
            return None, f"AI response format error: {e}"
        except (
            Exception
        ) as e:  # Catch Pydantic validation errors or other unexpected issues
            logger.error(
                f"Failed to validate/process AI response from {service_used}: {e}",
                exc_info=True,
            )
            logger.error(f"Raw response content was:\n{raw_response_str}")
            # Include details from Pydantic validation error if possible
            err_detail = str(e)
            if hasattr(e, "errors"):
                err_detail = json.dumps(e.errors(), indent=2)
            return None, f"AI response validation failed: {err_detail}"

    def _query_local(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """Sends request to local Ollama instance."""
        if not self.local_url:
            raise ConnectionError("Ollama URL not configured.")

        payload = {
            "model": self.ollama_model,
            "messages": messages,
            "stream": False,
            "format": "json",
        }
        logger.debug(
            f"Ollama request payload (messages omitted): { {k:v for k,v in payload.items() if k != 'messages'} }"
        )

        try:
            response = requests.post(
                f"{self.local_url}/api/chat",
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()  # Check for HTTP 4xx/5xx errors
            response_json = response.json()

            # Ollama's non-streaming JSON response structure
            if (
                (msg := response_json.get("message"))
                and isinstance(msg, dict)
                and (content := msg.get("content"))
            ):
                logger.debug(
                    f"Extracted local AI response content (length: {len(content)})"
                )
                return str(content)  # Ensure it's a string
            else:
                logger.error(
                    f"Unexpected response structure from local Ollama: {response_json}"
                )
                raise AIResponseError(
                    "Unexpected response structure from local Ollama."
                )

        except requests.Timeout:
            logger.error(
                f"Local Ollama request timed out after {self.timeout} seconds."
            )
            raise TimeoutError(f"Local LLM request timed out ({self.timeout}s)")
        except requests.RequestException as e:
            logger.error(f"Local Ollama request failed: {e}")
            raise ConnectionError(f"Failed to connect to local LLM: {e}")

    def _query_gemini(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """Sends request to Gemini via OpenAI compatible endpoint."""
        if not self.gemini_client:
            raise ConnectionError("Gemini client not initialized.")

        logger.debug(f"Gemini request using model: {self.gemini_model}")

        try:
            response = self.gemini_client.chat.completions.create(
                model=self.gemini_model,
                messages=messages,
                temperature=0.7,
                timeout=self.timeout,
            )
            if response.choices and (msg := response.choices[0].message):
                result = msg.content
                logger.debug(
                    f"Raw Gemini AI response received (length: {len(result or '')})"
                )
                return result
            else:
                logger.error(f"Unexpected response structure from Gemini: {response}")
                raise AIResponseError(
                    "No valid choice or message content received from Gemini."
                )

        except APITimeoutError:
            logger.error(f"Gemini request timed out after {self.timeout} seconds.")
            raise TimeoutError(f"Gemini request timed out ({self.timeout}s)")
        except APIConnectionError as e:
            logger.error(f"Gemini connection error: {e}")
            raise ConnectionError(f"Failed to connect to Gemini: {e}")
        except RateLimitError as e:
            logger.error(f"Gemini rate limit exceeded: {e}")
            # Consider specific handling like backoff/retry
            raise ConnectionError(f"Gemini rate limit exceeded: {e}")
        except APIStatusError as e:  # Catch HTTP errors from the API
            logger.error(
                f"Gemini API error: Status {e.status_code}, Response: {e.response.text}"
            )
            raise ConnectionError(
                f"Gemini API error (Status {e.status_code}): {e.body.get('message', 'Unknown error') if e.body else 'Unknown error'}"
            )
        except Exception as e:
            logger.error(f"Gemini API request failed unexpectedly: {e}", exc_info=True)
            raise RuntimeError(f"Gemini API error: {e}")

    # --- Methods to force switch (maybe for admin endpoint later) ---
    def switch_to_local(self) -> bool:
        """Force preference to local LLM and re-check availability."""
        logger.info("Switching AI preference to Local (Ollama).")
        self.use_local_preference = True
        self._local_checked = False  # Force re-check on next call
        return self._check_local_ollama()

    def switch_to_cloud(self) -> bool:
        """Force preference to Cloud (Gemini)."""
        logger.info("Switching AI preference to Cloud (Gemini).")
        self.use_local_preference = False
        return bool(self.gemini_client)  # Available if client is initialized
