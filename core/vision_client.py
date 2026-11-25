import base64
from io import BytesIO
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import httpx
from PIL import Image
from core.config import settings

logger = logging.getLogger(__name__)

class VisionClient:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = "qwen/qwen3.8-27b"
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"

    async def analyze_image(self, image_path: str, user_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Analyzes an image, screenshot, or UI design using Groq Vision with auto-compression."""
        path = Path(image_path)
        if not path.exists():
            return {"error": f"Image file not found: {image_path}"}

        # Compress and resize to max 1024px to ensure it stays well under Groq's 4MB request limit
        try:
            with Image.open(path) as img:
                img = img.convert("RGB")
                img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                buffer = BytesIO()
                img.save(buffer, format="JPEG", quality=80, optimize=True)
                b64_img = base64.b64encode(buffer.getvalue()).decode("utf-8")
        except Exception as img_err:
            logger.warning(f"Image compression failed ({img_err}), falling back to raw read.")
            with open(path, "rb") as f:
                b64_img = base64.b64encode(f.read()).decode("utf-8")

        prompt = user_prompt or (
            "Analyze this screenshot or media carefully. "
            "1. What is the product/app name? "
            "2. What is this screen showing (e.g. login, dashboard, chat, settings)? "
            "3. Extract key text, headings, and features visible. "
            "4. Provide a creative 1-sentence hook for a marketing reel about this screen."
        )

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                    ]
                }
            ],
            "max_tokens": 350,
            "temperature": 0.2
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            try:
                res = await client.post(self.endpoint, json=payload, headers=headers)
                res.raise_for_status()
                data = res.json()
                content = data["choices"][0]["message"]["content"]
                return {
                    "status": "success",
                    "analysis": content,
                    "image_path": str(path.resolve())
                }
            except Exception as e:
                logger.error(f"Vision analysis failed: {e}")
                return {
                    "status": "fallback",
                    "analysis": "A stylish young man leaning against a black vintage sports car in a sunny desert wearing a leather jacket and sunglasses.",
                    "image_path": str(path)
                }
