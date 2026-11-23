import json
import logging
from typing import Any, Dict, List, Optional
import httpx
from core.config import settings

logger = logging.getLogger(__name__)

import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional
import httpx
from core.config import settings

logger = logging.getLogger(__name__)

# Fallback models on Groq in case of rate-limiting (429)
GROQ_FALLBACK_MODELS = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b"
]

class LLMClient:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.timeout = 120.0

    def _get_provider_config(self, model_override: Optional[str] = None) -> Dict[str, Any]:
        """Resolves active LLM endpoint and headers."""
        if self.provider == "ollama":
            return {
                "base_url": settings.OLLAMA_BASE_URL.rstrip("/"),
                "api_key": "ollama",
                "model": model_override or settings.OLLAMA_MODEL,
                "headers": {"Content-Type": "application/json"}
            }
        elif self.provider == "groq":
            if not settings.GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY is not configured in .env")
            return {
                "base_url": "https://api.groq.com/openai/v1",
                "api_key": settings.GROQ_API_KEY,
                "model": model_override or settings.GROQ_MODEL,
                "headers": {
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0"
                }
            }
        elif self.provider == "gemini":
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is not configured in .env")
            return {
                "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
                "api_key": settings.GEMINI_API_KEY,
                "model": model_override or settings.GEMINI_MODEL,
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
        """Sends chat completion request with retry on 429 and automatic model failover."""
        candidate_models = [settings.GROQ_MODEL] if self.provider == "groq" else [None]
        if self.provider == "groq":
            for fb in GROQ_FALLBACK_MODELS:
                if fb not in candidate_models:
                    candidate_models.append(fb)

        last_error = None

        for model in candidate_models:
            cfg = self._get_provider_config(model_override=model)
            endpoint = f"{cfg['base_url']}/chat/completions"

            payload: Dict[str, Any] = {
                "model": cfg["model"],
                "messages": messages,
                "temperature": temperature,
            }
            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = "auto"

            # Try up to 3 retries with backoff on 429
            for attempt in range(3):
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    try:
                        res = await client.post(endpoint, json=payload, headers=cfg["headers"])
                        if res.status_code == 413:
                            logger.warning(f"Payload too large (413) on {cfg['model']}. Pruning message history and retrying...")
                            sys_msgs = [m for m in payload.get("messages", []) if m.get("role") == "system"]
                            user_msgs = [m for m in payload.get("messages", []) if m.get("role") == "user"]
                            payload["messages"] = (sys_msgs[:1] + user_msgs[-1:]) if user_msgs else sys_msgs
                            continue

                        if res.status_code == 429:
                            # Parse retry after
                            retry_after = 2.0
                            try:
                                err_data = res.json()
                                msg = err_data.get("error", {}).get("message", "")
                                match = re.search(r"try again in ([0-9\.]+)s", msg)
                                if match:
                                    retry_after = min(float(match.group(1)) + 0.5, 6.0)
                            except Exception:
                                pass

                            logger.warning(
                                f"Rate limited (429) on {cfg['model']} (attempt {attempt+1}/3). "
                                f"Retrying in {retry_after:.1f}s..."
                            )
                            await asyncio.sleep(retry_after)
                            continue

                        res.raise_for_status()
                        data = res.json()
                        choice = data["choices"][0]
                        return choice.get("message", {})

                    except httpx.ConnectError:
                        if self.provider == "ollama":
                            raise ConnectionError(
                                "Could not connect to local Ollama instance at http://localhost:11434."
                            )
                        raise
                    except httpx.HTTPStatusError as e:
                        last_error = e
                        if e.response.status_code == 429:
                            continue
                        logger.error(f"LLM API Error ({e.response.status_code}): {e.response.text}")
                        break

        # If all candidates exhausted, raise last error
        if last_error:
            raise last_error
        raise RuntimeError("Failed to complete LLM request after retries.")
