import json
import logging
from typing import Any, Dict, List, Optional
import httpx
from core.config import settings

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.timeout = 120.0

    def _get_provider_config(self) -> Dict[str, Any]:
        """Resolves active LLM endpoint and headers."""
        if self.provider == "ollama":
            return {
                "base_url": settings.OLLAMA_BASE_URL.rstrip("/"),
                "api_key": "ollama",
                "model": settings.OLLAMA_MODEL,
                "headers": {"Content-Type": "application/json"}
            }
        elif self.provider == "groq":
            if not settings.GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY is not configured in .env")
            return {
                "base_url": "https://api.groq.com/openai/v1",
                "api_key": settings.GROQ_API_KEY,
                "model": settings.GROQ_MODEL,
                "headers": {
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
            }
        elif self.provider == "gemini":
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is not configured in .env")
            return {
                "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
                "api_key": settings.GEMINI_API_KEY,
                "model": settings.GEMINI_MODEL,
                "headers": {
                    "Authorization": f"Bearer {settings.GEMINI_API_KEY}",
                    "Content-Type": "application/json"
                }
            }
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """Sends chat completion request with optional tool calling."""
        cfg = self._get_provider_config()
        endpoint = f"{cfg['base_url']}/chat/completions"

        payload: Dict[str, Any] = {
            "model": cfg["model"],
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                res = await client.post(endpoint, json=payload, headers=cfg["headers"])
                res.raise_for_status()
                data = res.json()
                choice = data["choices"][0]
                message = choice.get("message", {})
                return message
            except httpx.ConnectError:
                if self.provider == "ollama":
                    raise ConnectionError(
                        "Could not connect to local Ollama instance at http://localhost:11434. "
                        "Please run 'ollama serve' or configure GROQ_API_KEY/GEMINI_API_KEY in .env."
                    )
                raise
            except httpx.HTTPStatusError as e:
                logger.error(f"LLM API Error ({e.response.status_code}): {e.response.text}")
                raise
