"""
AI generation utilities using FREE APIs.
Priority: Gemini (best for Thai + authority content) > Groq > Ollama
"""

import os
import json
import logging
import time
import requests
from typing import Optional, List, Dict, Any
from pathlib import Path
from .utils import print_error, print_success, print_warning
from .config import get_config

# APIManager is optional - not needed for basic usage
# Projects can use .env files directly for API keys
API_MANAGER_AVAILABLE = False
APIManager = None


class GeminiClient:
    """
    Client for Google Gemini API (FREE - 1.5M requests/day).
    Best for Thai language and authority content.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-pro",
        logger: Optional[logging.Logger] = None,
        api_manager: Optional[Any] = None,
        key_name: Optional[str] = None,
    ):
        """
        Initialize Gemini client.

        Args:
            api_key: Google API key (free from aistudio.google.com)
            model: Model name (gemini-1.5-pro, gemini-1.5-flash)
            logger: Logger instance
            api_manager: APIManager instance for key rotation
            key_name: Name of the API key (for tracking in WORLD_STATE)
        """
        self.api_key = api_key
        self.model = model
        self.logger = logger or logging.getLogger(__name__)
        self.api_manager = api_manager
        self.key_name = key_name
        # Important: Use full model path (models/gemini-2.5-pro)
        self.base_url = (
            f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent"
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> Optional[str]:
        """
        Send chat request to Gemini.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            json_mode: Whether to force JSON output

        Returns:
            Generated text or None
        """
        try:
            # Convert messages to Gemini format
            contents = []
            system_instruction = None

            for msg in messages:
                role = msg["role"]
                content = msg["content"]

                if role == "system":
                    system_instruction = content
                elif role == "user":
                    contents.append({"role": "user", "parts": [{"text": content}]})
                elif role == "assistant":
                    contents.append({"role": "model", "parts": [{"text": content}]})

            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature,
                    "topP": 0.95,
                    "topK": 40,
                },
            }

            if max_tokens:
                payload["generationConfig"]["maxOutputTokens"] = max_tokens

            if json_mode:
                payload["generationConfig"]["responseMimeType"] = "application/json"

            if system_instruction:
                payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

            url = f"{self.base_url}?key={self.api_key}"

            try:
                # Built-in retry for 429 rate limit errors
                max_retries = 3
                for attempt in range(max_retries):
                    response = requests.post(url, json=payload, timeout=60)
                    if response.status_code == 429 and attempt < max_retries - 1:
                        wait_time = (2**attempt) * 5  # 5s, 10s, 20s
                        self.logger.warning(
                            f"Rate limit (429) hit, waiting {wait_time}s before retry {attempt + 1}/{max_retries - 1}..."
                        )
                        time.sleep(wait_time)
                        continue
                    response.raise_for_status()
                    break

                # Mark success if we have APIManager
                if self.api_manager and self.key_name:
                    self.api_manager.mark_api_success("GOOGLE_GEMINI", self.key_name)

            except Exception as e:
                error_msg = str(e)
                self.logger.error(f"Gemini request failed: {error_msg}")

                # If we have APIManager, use smart retry with exponential backoff
                if self.api_manager and self.key_name:
                    # Mark current key as failed
                    self.api_manager.mark_api_failed(
                        "GOOGLE_GEMINI", self.key_name, error_msg
                    )

                    # Check if it's a rate limit error for better logging
                    is_rate_limit = self.api_manager.detect_rate_limit(error_msg)
                    if is_rate_limit:
                        self.logger.warning(
                            "Rate limit detected - using smart rotation"
                        )

                    # Use rotate_with_retry (max 2 retries with exponential backoff)
                    next_key = self.api_manager.rotate_with_retry(
                        "GOOGLE_GEMINI", max_retries=2
                    )

                    if next_key:
                        self.logger.info(f"Switched to key: {next_key['name']}")
                        self.api_key = next_key["key"]
                        self.key_name = next_key["name"]
                        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/{self.model}:generateContent"

                        # Retry with new key
                        url = f"{self.base_url}?key={self.api_key}"
                        try:
                            response = requests.post(url, json=payload, timeout=60)
                            response.raise_for_status()

                            # Mark new key as successful
                            self.api_manager.mark_api_success(
                                "GOOGLE_GEMINI", self.key_name
                            )
                        except Exception as retry_error:
                            self.logger.error(f"Retry failed: {retry_error}")
                            self.api_manager.mark_api_failed(
                                "GOOGLE_GEMINI", self.key_name, str(retry_error)
                            )
                            return None
                    else:
                        self.logger.error("All API keys exhausted!")
                        return None
                else:
                    return None

            result = response.json()

            # Extract text from response
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if len(parts) > 0 and "text" in parts[0]:
                        return parts[0]["text"]

            self.logger.error(f"Unexpected Gemini response format: {result}")
            return None

        except requests.exceptions.Timeout:
            self.logger.error("Gemini request timeout (60s)")
            return None
        except Exception as e:
            if "response" in locals() and hasattr(response, "text"):
                self.logger.error(f"Gemini error response: {response.text}")
            self.logger.error(f"Gemini request failed: {e}")
            return None

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> Optional[str]:
        """Simple text generation."""
        messages = []

        if system:
            messages.append({"role": "system", "content": system})

        messages.append({"role": "user", "content": prompt})

        return self.chat(messages, temperature=temperature, json_mode=json_mode)


class OllamaClient:
    """
    Client for Ollama local LLM (100% Free).
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2",
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize Ollama client.

        Args:
            base_url: Ollama server URL
            model: Model name (llama3.2, typhoon-thai, etc.)
            logger: Logger instance
        """
        self.base_url = base_url
        self.model = model
        self.logger = logger or logging.getLogger(__name__)

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> Optional[str]:
        """
        Send chat request to Ollama.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            json_mode: Whether to request JSON output (adds instruction to prompt)

        Returns:
            Generated text or None if failed
        """
        try:
            url = f"{self.base_url}/api/chat"

            # If json_mode is enabled, add JSON instruction to the last user message
            modified_messages = messages.copy()
            if json_mode and modified_messages:
                last_msg = modified_messages[-1]
                if last_msg.get("role") == "user":
                    modified_messages[-1] = {
                        "role": "user",
                        "content": last_msg["content"]
                        + "\n\nIMPORTANT: Return ONLY valid JSON format. Do not include any markdown formatting or explanations.",
                    }

            payload = {
                "model": self.model,
                "messages": modified_messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                },
            }

            if max_tokens:
                payload["options"]["num_predict"] = max_tokens

            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()

            result = response.json()
            return result["message"]["content"]

        except requests.exceptions.ConnectionError:
            self.logger.error("Cannot connect to Ollama. Is it running?")
            print_error("Ollama not running. Start with: ollama serve")
            return None
        except Exception as e:
            self.logger.error(f"Ollama request failed: {e}")
            return None

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> Optional[str]:
        """
        Simple text generation.

        Args:
            prompt: User prompt
            system: System message
            temperature: Sampling temperature
            json_mode: Whether to request JSON output

        Returns:
            Generated text
        """
        messages = []

        if system:
            messages.append({"role": "system", "content": system})

        messages.append({"role": "user", "content": prompt})

        return self.chat(messages, temperature=temperature, json_mode=json_mode)

    def is_available(self) -> bool:
        """
        Check if Ollama is running and model is available.

        Returns:
            True if available
        """
        try:
            url = f"{self.base_url}/api/tags"
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            models = response.json().get("models", [])
            model_names = [m["name"].split(":")[0] for m in models]

            if self.model not in model_names:
                print_warning(
                    f"Model '{self.model}' not found. Run: ollama pull {self.model}"
                )
                return False

            return True

        except Exception as e:
            self.logger.warning(f"Ollama not available: {e}")
            return False


class GroqClient:
    """
    Client for Groq API (Free Tier - 30 req/min).
    """

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.1-8b-instant",
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize Groq client.

        Args:
            api_key: Groq API key (free)
            model: Model name
            logger: Logger instance
        """
        self.api_key = api_key
        self.model = model
        self.logger = logger or logging.getLogger(__name__)
        self.base_url = "https://api.groq.com/openai/v1"

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> Optional[str]:
        """
        Send chat request to Groq.

        Args:
            messages: List of message dicts
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            json_mode: Whether to request JSON output via response_format

        Returns:
            Generated text or None
        """
        try:
            url = f"{self.base_url}/chat/completions"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }

            if max_tokens:
                payload["max_tokens"] = max_tokens

            if json_mode:
                payload["response_format"] = {"type": "json_object"}

            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except Exception as e:
            if "response" in locals() and hasattr(response, "text"):
                self.logger.error(f"Groq error response: {response.text}")
            self.logger.error(f"Groq request failed: {e}")
            return None

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> Optional[str]:
        """Simple text generation."""
        messages = []

        if system:
            messages.append({"role": "system", "content": system})

        messages.append({"role": "user", "content": prompt})

        return self.chat(messages, temperature=temperature, json_mode=json_mode)


class OpenRouterClient:
    """
    Client for OpenRouter API.
    Access to various models (DeepSeek, Claude, Gemini, Llama).
    """

    def __init__(
        self,
        api_key: str,
        model: str = "google/gemini-2.0-flash-001",
        logger: Optional[logging.Logger] = None,
    ):
        self.api_key = api_key
        self.model = model
        self.logger = logger or logging.getLogger(__name__)
        self.base_url = "https://openrouter.ai/api/v1"

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> Optional[str]:
        try:
            url = f"{self.base_url}/chat/completions"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://openclaw.dev",
                "X-Title": "OpenClaw Agent",
            }

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }

            if max_tokens:
                payload["max_tokens"] = max_tokens

            if json_mode:
                payload["response_format"] = {"type": "json_object"}

            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except Exception as e:
            if "response" in locals() and hasattr(response, "text"):
                self.logger.error(f"OpenRouter error response: {response.text}")
            self.logger.error(f"OpenRouter request failed: {e}")
            return None

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> Optional[str]:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages, temperature=temperature, json_mode=json_mode)

    def generate_image(self, prompt: str) -> Optional[str]:
        """Generate image using OpenRouter (if supported model) or fallback."""
        # OpenRouter text models don't generate images directly.
        # For now, return None so pipeline skips or handles it.
        # Future: Integrate specific image model on OpenRouter if available.
        return None


class AnthropicClient:
    """
    Client for Anthropic Claude API (Claude 4.6 Sonnet).
    Best for Thai language and high-quality content.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        logger: Optional[logging.Logger] = None,
    ):
        self.api_key = api_key
        self.model = model
        self.logger = logger or logging.getLogger(__name__)
        self.base_url = "https://api.anthropic.com/v1"

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> Optional[str]:
        try:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }

            # Convert messages to Anthropic format
            anthropic_messages = []
            system_msg = None

            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    anthropic_messages.append(
                        {"role": msg["role"], "content": msg["content"]}
                    )

            payload = {
                "model": self.model,
                "messages": anthropic_messages,
                "temperature": temperature,
            }

            if max_tokens:
                payload["max_tokens"] = max_tokens
            else:
                payload["max_tokens"] = 4096

            if json_mode:
                payload["system"] = (
                    system_msg or ""
                ) + "\n\nRespond ONLY with valid JSON."
            elif system_msg:
                payload["system"] = system_msg

            response = requests.post(
                f"{self.base_url}/messages", headers=headers, json=payload, timeout=120
            )
            response.raise_for_status()

            result = response.json()
            return result["content"][0]["text"]

        except Exception as e:
            if "response" in locals() and hasattr(response, "text"):
                self.logger.error(f"Anthropic error response: {response.text}")
            self.logger.error(f"Anthropic request failed: {e}")
            return None

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> Optional[str]:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages, temperature=temperature, json_mode=json_mode)


def create_ai_client(logger: Optional[logging.Logger] = None):
    """
    Create AI client using available option.
    Priority: OpenRouter > Gemini > Groq > Ollama
    """
    config = get_config()

    # Initialize APIManager
    api_manager = None
    if API_MANAGER_AVAILABLE:
        try:
            api_manager = APIManager(
                settings_path=config.get_master_settings_path(),
                state_path=config.get_world_state_path(),
                logger=logger,
            )
        except Exception as e:
            if logger:
                logger.error(f"Failed to initialize APIManager: {e}")
            print_error(f"Failed to initialize APIManager: {e}")

    # Option 1: OpenRouter (PRIMARY - All AI including Claude Sonnet via OpenRouter)
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-20250514")
        print_success(f"Using OpenRouter ({model})")
        return OpenRouterClient(api_key=openrouter_key, model=model, logger=logger)
    if openrouter_key:
        print_success("Using OpenRouter (Gemini 2.0 Flash)")
        return OpenRouterClient(
            api_key=openrouter_key, model="google/gemini-2.0-flash-001", logger=logger
        )

    # Option 2: OpenRouter via APIManager (if available)
    if api_manager:
        key_data = api_manager.get_active_api_key("OPENROUTER")
        if key_data and key_data.get("key"):
            print_success(
                f"Using OpenRouter (Gemini 2.0 Flash) - Key: {key_data['name']}"
            )
            return OpenRouterClient(
                api_key=key_data["key"],
                model="google/gemini-2.0-flash-001",
                logger=logger,
            )

    # Option 3: Google Gemini API (Fallback)
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if gemini_key:
        print_success("Using Google Gemini 2.5 Flash (Env Var)")
        return GeminiClient(
            api_key=gemini_key, model="models/gemini-2.5-flash", logger=logger
        )

    # Option 4: Google Gemini API via APIManager
    if api_manager:
        key_data = api_manager.get_active_api_key("GOOGLE_GEMINI")
        if key_data and key_data.get("key"):
            print_success(f"Using Google Gemini 2.5 Flash - Key: {key_data['name']}")
            return GeminiClient(
                api_key=key_data["key"],
                model="models/gemini-2.5-flash",
                logger=logger,
                api_manager=api_manager,
                key_name=key_data["name"],
            )

    # Option 3: Groq API
    if api_manager:
        key_data = api_manager.get_active_api_key("GROQ")
        if key_data and key_data.get("key"):
            print_success(f"Using Groq API - Key: {key_data['name']}")
            return GroqClient(
                api_key=key_data["key"], model="llama-3.3-70b-versatile", logger=logger
            )

    # Legacy Environment Variable Fallback (for backward compatibility)
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        print_success("Using Groq API (Env Var)")
        return GroqClient(
            api_key=groq_key, model="llama-3.3-70b-versatile", logger=logger
        )

    # Option 5: Anthropic Claude (PRIMARY for Lookforward & Shopee)
    anthropic_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_KEY")
    if anthropic_key:
        print_success("Using Anthropic Claude Sonnet 4.6")
        return AnthropicClient(
            api_key=anthropic_key, model="claude-sonnet-4-20250514", logger=logger
        )

    # Option 4: Ollama
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")

    ollama = OllamaClient(base_url=ollama_url, model=ollama_model, logger=logger)
    if ollama.is_available():
        print_success(f"Using Ollama ({ollama_model}) - 100% FREE!")
        return ollama

    print_error("No AI client available!")
    return None
