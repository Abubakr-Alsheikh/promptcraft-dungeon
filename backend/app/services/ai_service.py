import json
import string
import requests
import logging
from typing import Dict, Any, List, Optional, Tuple
from ..schemas.ai_responses import AIResponse
from flask import current_app
from openai import (
    OpenAI,
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
    APIStatusError,
)


logger = logging.getLogger(__name__)


# Custom Exception for AI Service issues
class AIResponseError(Exception):
    """Custom exception for errors during AI response generation or parsing."""

    pass


class AIService:
    """
    Handles interactions with AI language models (local Ollama or cloud-based Gemini).
    Manages model selection, prompt formatting, API calls, and response parsing.
    Includes specific fallback logic for Gemini 403 errors.
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
            # Use a simple request to the base URL
            response = requests.get(f"{self.local_url}/", timeout=5)
            response.raise_for_status()  # Check for HTTP errors 4xx/5xx

            # Check if the specific model is available
            try:
                tags_response = requests.get(f"{self.local_url}/api/tags", timeout=5)
                if tags_response.ok:
                    models = tags_response.json().get("models", [])
                    if not any(m["name"] == self.ollama_model for m in models):
                        logger.warning(
                            f"Ollama instance at {self.local_url} is up, but model '{self.ollama_model}' not found."
                        )
                else:
                    logger.warning(
                        f"Could not verify model list from Ollama at {self.local_url}/api/tags (Status: {tags_response.status_code})"
                    )
            except requests.RequestException as tags_e:
                logger.warning(f"Failed to check Ollama tags endpoint: {tags_e}")
                # Proceed assuming base URL check was sufficient if tags check fails

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
            self._local_checked = True  # Mark as checked

        return self._local_available

    def _format_system_prompt(self, system_template: str, context: dict) -> str:
        """Safely formats the system prompt template with available context."""
        try:
            template_keys = {
                fname
                for _, fname, _, _ in string.Formatter().parse(system_template)
                if fname
            }
            filtered_context = {k: v for k, v in context.items() if k in template_keys}
            for key in template_keys:
                filtered_context.setdefault(key, f"<{key}_unavailable>")
            return system_template.format(**filtered_context)
        except Exception as e:
            logger.error(
                f"Error formatting system prompt: {e}. Using raw template.",
                exc_info=True,
            )
            return system_template

    def generate_structured_response(
        self,
        system_prompt_template: str,
        history: List[Dict[str, str]],
        user_command: str,
        context: Dict[str, Any],
    ) -> Tuple[Optional[AIResponse], Optional[str]]:
        """
        Generates a structured response, attempting primary AI, with specific fallback
        from Gemini 403 error to local Ollama.
        """
        system_prompt = self._format_system_prompt(system_prompt_template, context)
        logger.debug(f"Using System Prompt (first 200 chars): {system_prompt[:200]}...")
        logger.debug(f"Current User Command: {user_command}")
        logger.debug(f"Processing with History (length): {len(history)}")

        messages = (
            [{"role": "system", "content": system_prompt}]
            + history
            + [{"role": "user", "content": user_command}]
        )

        raw_response_str: Optional[str] = None
        error_message: Optional[str] = None
        service_used: str = "None"
        attempt_local_fallback: bool = False
        gemini_403_error_msg: Optional[str] = None

        # --- Determine primary service and attempt ---
        use_local_initially = (
            self.use_local_preference and self.local_url and self._check_local_ollama()
        )

        if use_local_initially:
            primary_service = "Ollama"
            service_used = f"Ollama ({self.ollama_model})"
            logger.info(f"Attempting query to primary: {service_used}")
            try:
                raw_response_str = self._query_local(messages)
            except (ConnectionError, TimeoutError, AIResponseError, Exception) as e:
                logger.warning(
                    f"Primary local Ollama query failed: {e}. Will attempt fallback to Gemini.",
                    exc_info=True,
                )
                error_message = f"Local AI ({self.ollama_model}) failed: {e}. "
                # Fall through to try Gemini if available
        else:
            primary_service = "Gemini"
            if self.gemini_client:
                service_used = f"Gemini ({self.gemini_model})"
                logger.info(f"Attempting query to primary: {service_used}")
                try:
                    raw_response_str = self._query_gemini(messages)
                    error_message = (
                        None  # Clear any previous potential error if successful
                    )
                except APIStatusError as e:
                    logger.error(
                        f"Gemini API error: Status {e.status_code}, Response: {e.response.text}",
                        exc_info=True,  # Log full trace for status errors
                    )
                    gemini_err_detail = f"Gemini API error (Status {e.status_code}): {(e.body or 'No details')}"
                    if e.status_code == 403:
                        logger.warning(
                            f"Gemini returned 403 Forbidden. Will attempt fallback to local Ollama if available."
                        )
                        # Set flag to attempt local fallback *after* this block
                        attempt_local_fallback = True
                        gemini_403_error_msg = (
                            gemini_err_detail  # Store the specific 403 error
                        )
                        error_message = (
                            gemini_err_detail  # Keep error in case fallback fails
                        )
                    else:
                        # Handle other Gemini API errors (non-403)
                        error_message = gemini_err_detail
                        raw_response_str = None  # Ensure no partial response
                except (
                    APITimeoutError,
                    APIConnectionError,
                    RateLimitError,
                    Exception,
                ) as e:
                    # Handle other Gemini connection/timeout/rate limit errors
                    logger.error(f"Gemini query failed: {e}", exc_info=True)
                    error_message = (
                        error_message or ""
                    ) + f"Cloud AI ({self.gemini_model}) failed: {e}"
                    raw_response_str = None  # Ensure no partial response
            else:
                # Gemini was preferred/primary but not configured/initialized
                logger.error(
                    "Gemini is the preferred service, but the client is not available."
                )
                error_message = (
                    "Cloud AI service (Gemini) is not configured or available."
                )

        # --- Handle Fallbacks ---

        # Fallback 1: From Local failure to Gemini
        if primary_service == "Ollama" and raw_response_str is None:  # If local failed
            if self.gemini_client:
                service_used = f"Gemini ({self.gemini_model})"
                logger.info(
                    f"Attempting fallback query to {service_used} after local failure."
                )
                try:
                    raw_response_str = self._query_gemini(messages)
                    # If Gemini succeeds, clear the local error message
                    error_message = None
                except APIStatusError as e:
                    # Handle Gemini errors during fallback, including 403
                    # We won't fallback again from Gemini 403 here, as local already failed
                    logger.error(
                        f"Fallback Gemini API error: Status {e.status_code}, Response: {e.response.text}",
                        exc_info=True,
                    )
                    gemini_err_detail = f"Fallback Cloud AI ({self.gemini_model}) also failed - Gemini API error (Status {e.status_code}): {e.body or 'No details'}"
                    # Combine with original local error
                    error_message = (
                        error_message or "Local AI failed. "
                    ) + gemini_err_detail
                    raw_response_str = None
                except (
                    APITimeoutError,
                    APIConnectionError,
                    RateLimitError,
                    Exception,
                ) as e:
                    logger.error(f"Fallback Gemini query failed: {e}", exc_info=True)
                    # Combine with original local error
                    error_message = (
                        error_message or "Local AI failed. "
                    ) + f"Fallback Cloud AI ({self.gemini_model}) also failed: {e}"
                    raw_response_str = None
            else:
                # Local failed and no Gemini client available for fallback
                logger.error(
                    "Local Ollama failed, and no Gemini client available for fallback."
                )
                # Keep the original error_message from the local failure

        # Fallback 2: From Gemini 403 failure to Local (Specific Case)
        elif attempt_local_fallback:  # This flag is only true if Gemini returned 403
            if self.local_url and self._check_local_ollama():
                service_used = f"Ollama ({self.ollama_model})"
                logger.info(
                    f"Attempting fallback query to {service_used} after Gemini 403."
                )
                try:
                    raw_response_str = self._query_local(messages)
                    # If local succeeds, clear the Gemini 403 error message
                    logger.info(f"Local fallback successful after Gemini 403.")
                    error_message = None
                    service_used += (
                        " (fallback)"  # Indicate fallback in logs/final message
                    )
                except (ConnectionError, TimeoutError, AIResponseError, Exception) as e:
                    logger.error(
                        f"Local Ollama fallback query failed after Gemini 403: {e}",
                        exc_info=True,
                    )
                    # Keep the original Gemini 403 error and append the local failure reason
                    error_message = f"{gemini_403_error_msg}. Fallback to Local AI ({self.ollama_model}) also failed: {e}"
                    raw_response_str = None
            else:
                # Gemini had 403, but local is not available for fallback
                logger.warning(
                    "Gemini returned 403, but local Ollama is not configured or available for fallback."
                )
                # Keep the gemini_403_error_msg as the main error
                error_message = gemini_403_error_msg

        # --- Final Check and Parse ---
        if raw_response_str is None:
            final_error_msg = (
                error_message or "AI query failed, but no specific error was captured."
            )
            logger.error(
                f"AI response generation failed. Final error: {final_error_msg}"
            )
            return None, final_error_msg

        # --- Parse and Validate the Successful Response ---
        try:
            logger.debug(
                f"Raw AI response from {service_used}:\n{raw_response_str[:500]}..."
            )
            cleaned_response_str = self._clean_raw_response(raw_response_str)

            if cleaned_response_str is None:
                raise AIResponseError(
                    "Response was not valid JSON and no JSON block could be extracted."
                )

            response_data = json.loads(cleaned_response_str)
            ai_response_obj = AIResponse.model_validate(response_data)
            logger.debug(f"Successfully parsed AI response from {service_used}.")
            return ai_response_obj, None  # Success

        except (json.JSONDecodeError, AIResponseError, Exception) as e:
            # Catch JSON errors, our custom error, Pydantic validation errors etc.
            logger.error(
                f"Failed to decode JSON response from {service_used}: {e}",
                exc_info=True,
            )
            logger.error(f"Raw response content was:\n{raw_response_str}")
            return None, f"AI response JSON decode failed ({service_used}): {str(e)}"
        except AIResponseError as e:
            logger.error(
                f"Failed to validate AI response from {service_used}: {e}",
                exc_info=True,
            )
            logger.error(f"Raw response content was:\n{raw_response_str}")
            return None, f"AI response validation failed ({service_used}): {str(e)}"
        except ValueError as e:
            logger.error(
                f"Failed to process AI response from {service_used}: {e}",
                exc_info=True,
            )
            logger.error(f"Raw response content was:\n{raw_response_str}")
            err_detail = str(e)
            if hasattr(e, "errors"):  # Try to get Pydantic validation details
                try:
                    err_detail = json.dumps(e.errors(), indent=2)
                except Exception:
                    pass  # Keep original str(e) if errors() fails

            return None, f"AI response processing failed ({service_used}): {err_detail}"

    def _clean_raw_response(self, raw_response_str: str) -> Optional[str]:
        """Attempts to clean and extract a JSON string from the raw AI response."""
        cleaned = raw_response_str.strip()

        # Handle markdown code blocks ```json ... ``` or ``` ... ```
        if cleaned.startswith("```"):
            # Remove opening ```, optional language specifier (like json) and newline
            cleaned = cleaned.split("\n", 1)[-1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()  # Remove closing ``` and strip again

        # If it looks like JSON now, return it
        if cleaned.startswith("{") and cleaned.endswith("}"):
            return cleaned
        elif cleaned.startswith("[") and cleaned.endswith("]"):  # Allow JSON arrays too
            return cleaned

        # If not clearly JSON, try to find the first '{' and last '}'
        logger.warning(
            f"AI response does not appear to be clean JSON. Content starts: {cleaned[:100]}..."
        )
        json_start = cleaned.find("{")
        json_end = cleaned.rfind("}")
        if json_start != -1 and json_end != -1 and json_start < json_end:
            extracted = cleaned[json_start : json_end + 1]
            # Basic check if the extracted part might be valid JSON
            try:
                json.loads(extracted)  # Test parse
                logger.info(
                    "Attempting to use extracted JSON block from non-JSON response."
                )
                return extracted
            except json.JSONDecodeError:
                logger.warning(
                    f"Extracted block '{extracted[:100]}...' is not valid JSON."
                )
                return None  # Extraction failed validation

        logger.error(
            f"Could not find or extract a valid JSON object from the response."
        )
        return None

    def _query_local(self, messages: List[Dict[str, str]]) -> str:
        """Sends request to local Ollama instance. Raises errors on failure."""
        if not self.local_url:
            raise ConnectionError("Ollama URL not configured.")

        payload = {
            "model": self.ollama_model,
            "messages": messages,
            "stream": False,
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
            response.raise_for_status()  # Raises HTTPError for 4xx/5xx
            response_json = response.json()

            logger.debug(f"Full Ollama raw JSON response: {response_json}")
            # Ollama's non-streaming JSON response structure
            if (
                (msg := response_json.get("message"))
                and isinstance(msg, dict)
                and (content := msg.get("content"))
            ):
                logger.debug(
                    f"Extracted local AI response content (length: {len(content)})"
                )
                return str(content)
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
        except requests.HTTPError as e:
            # Catch specific HTTP errors from Ollama
            logger.error(
                f"Local Ollama request failed with HTTP Status {e.response.status_code}: {e.response.text}"
            )
            raise ConnectionError(
                f"Local LLM HTTP error {e.response.status_code}: {e.response.text[:200]}"
            )  # Include snippet
        except requests.RequestException as e:
            logger.error(f"Local Ollama communication failed: {e}")
            raise ConnectionError(f"Failed to connect to local LLM: {e}")
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during local Ollama query: {e}",
                exc_info=True,
            )
            raise  # Re-raise unexpected errors

    def _query_gemini(self, messages: List[Dict[str, str]]) -> str:
        """
        Sends request to Gemini via OpenAI compatible endpoint.
        Raises specific OpenAI/HTTP errors on failure.
        """
        if not self.gemini_client:
            raise ConnectionError("Gemini client not initialized.")

        processed_messages = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            # Basic validation/cleaning
            if role in ["user", "assistant", "system"] and isinstance(content, str):
                processed_messages.append({"role": role, "content": content})
            else:
                logger.warning(f"Skipping invalid message format in history: {msg}")

        logger.debug(
            f"Gemini request using model: {self.gemini_model}. Message count: {len(processed_messages)}"
        )

        try:
            completion_params = {
                "model": self.gemini_model,
                "messages": processed_messages,
                "timeout": self.timeout,
            }

            response = self.gemini_client.chat.completions.create(**completion_params)

            if (
                response.choices
                and (choice := response.choices[0])
                and (msg := choice.message)
                and (result := msg.content)
            ):
                # Log finish reason if available (e.g., 'stop', 'length', 'content_filter')
                finish_reason = choice.finish_reason
                logger.debug(
                    f"Raw Gemini AI response received (length: {len(result)}). Finish reason: {finish_reason}"
                )
                if finish_reason == "content_filter":
                    logger.warning(
                        "Gemini response was blocked due to content filtering."
                    )
                    raise AIResponseError("Gemini response blocked by content filter.")
                elif finish_reason == "length":
                    logger.warning(
                        "Gemini response may be truncated due to length limits."
                    )
                    # Proceed with the truncated response for now.

                return result
            else:
                logger.error(
                    f"Unexpected response structure or empty content from Gemini: {response}"
                )
                raise AIResponseError(
                    "No valid choice or message content received from Gemini."
                )
        except APIStatusError as e:
            # This will be caught and handled (including 403 check) in generate_structured_response
            logger.warning(
                f"Gemini APIStatusError encountered (Status {e.status_code}). Will be handled by caller."
            )
            raise  # Re-raise for the caller to handle the specific status code
        except APITimeoutError:
            logger.error(f"Gemini request timed out after {self.timeout} seconds.")
            raise TimeoutError(
                f"Gemini request timed out ({self.timeout}s)"
            )  # Raise standard TimeoutError
        except (RateLimitError, APIConnectionError) as e:
            # Let caller handle these specific connection/rate limit issues
            logger.error(f"Gemini connection/rate limit error: {e}")
            raise ConnectionError(
                f"Gemini API error: {e}"
            )  # Raise standard ConnectionError
        except Exception as e:
            # Catch any other unexpected errors during the API call
            logger.error(f"Gemini API request failed unexpectedly: {e}", exc_info=True)
            # Wrap in a runtime error or re-raise depending on desired higher-level handling
            raise RuntimeError(f"Unexpected Gemini API error: {e}")

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
        # Cloud is available if the client was successfully initialized
        is_available = bool(self.gemini_client)
        if not is_available:
            logger.warning(
                "Attempted to switch to Cloud (Gemini), but client is not initialized/available."
            )
        return is_available
