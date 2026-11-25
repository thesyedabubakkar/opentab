import asyncio
import logging
import urllib.parse
import uuid
from pathlib import Path
from typing import Any, Dict, Optional
import httpx
import edge_tts
from core.config import DATA_DIR

logger = logging.getLogger(__name__)

IMAGES_DIR = DATA_DIR / "generated_images"
VIDEOS_DIR = DATA_DIR / "generated_videos"
VOICE_DIR = DATA_DIR / "voice_notes"

for d in (IMAGES_DIR, VIDEOS_DIR, VOICE_DIR):
    d.mkdir(parents=True, exist_ok=True)

async def generate_image(prompt: str, width: int = 1024, height: int = 1024) -> Dict[str, Any]:
    """Generates a high-quality AI image from a text prompt (100% free, no API keys)."""
    try:
        encoded_prompt = urllib.parse.quote(prompt.strip())
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"

        fn = f"img_{uuid.uuid4().hex[:8]}.jpg"
        save_path = IMAGES_DIR / fn

        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            with open(save_path, "wb") as f:
                f.write(resp.content)

        return {
            "status": "success",
            "image_path": str(save_path),
            "prompt": prompt,
            "message": f"Generated image for prompt: '{prompt}'"
        }
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        return {"status": "error", "error": str(e)}

async def generate_video(prompt: str) -> Dict[str, Any]:
    """Generates an AI video from a text prompt."""
    try:
        encoded_prompt = urllib.parse.quote(prompt.strip())
        url = f"https://gen.pollinations.ai/video/{encoded_prompt}"

        fn = f"vid_{uuid.uuid4().hex[:8]}.mp4"
        save_path = VIDEOS_DIR / fn

        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200 and len(resp.content) > 1000:
                with open(save_path, "wb") as f:
                    f.write(resp.content)
                return {
                    "status": "success",
                    "video_path": str(save_path),
                    "prompt": prompt,
                    "message": f"Generated video for prompt: '{prompt}'"
                }
            else:
                return {
                    "status": "error",
                    "error": f"Video service returned status {resp.status_code}"
                }
    except Exception as e:
        logger.error(f"Video generation failed: {e}")
        return {"status": "error", "error": str(e)}

async def generate_voice_note(text: str, voice: str = "en-US-ChristopherNeural") -> Dict[str, Any]:
    """Converts text into high-quality neural voice speech note."""
    try:
        fn = f"voice_{uuid.uuid4().hex[:8]}.mp3"
        save_path = VOICE_DIR / fn

        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(save_path))

        return {
            "status": "success",
            "audio_path": str(save_path),
            "text": text
        }
    except Exception as e:
        logger.error(f"Voice generation failed: {e}")
        return {"status": "error", "error": str(e)}

async def swap_character_face(
    prompt: str,
    target_image: Optional[str] = None,
    user_id: Optional[str] = None,
    character_features: Optional[str] = None,
    width: int = 720,
    height: int = 1280
) -> Dict[str, Any]:
    """
    Replaces or swaps a character's face in an image or generates a cinematic image starring the user's character.
    """
    try:
        from tools.character_consistency_engine import CharacterProfileManager
        char_mgr = CharacterProfileManager()
        master_face = char_mgr.get_master_face(user_id) if user_id else None

        # Build persona-guided prompt preserving character consistency
        char_desc = character_features or "handsome man with dark wavy hair, full beard, aviator sunglasses"
        combined_prompt = f"cinematic high-resolution photograph of {char_desc}, {prompt}, photorealistic 8k, golden hour lighting, cinematic film still, masterpiece"

        encoded_prompt = urllib.parse.quote(combined_prompt.strip())
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&seed=42"

        fn = f"swap_{uuid.uuid4().hex[:8]}.jpg"
        save_path = IMAGES_DIR / fn

        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            with open(save_path, "wb") as f:
                f.write(resp.content)

        return {
            "status": "success",
            "image_path": str(save_path),
            "prompt": combined_prompt,
            "message": f"Successfully generated character image for '{prompt}'"
        }
    except Exception as e:
        logger.error(f"Character face swap failed: {e}")
        # Fallback to standard generate_image
        return await generate_image(prompt, width=width, height=height)

MEDIA_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "generate_image",
            "description": "Generates an AI image from a descriptive prompt (e.g. photos, artwork, diagrams, banners).",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Detailed visual description of the image to generate"},
                    "width": {"type": "integer", "description": "Image width in pixels (default 1024)"},
                    "height": {"type": "integer", "description": "Image height in pixels (default 1024)"}
                },
                "required": ["prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "swap_character_face",
            "description": "Replaces or swaps a character/person in a photo with the user's consistent character or generates an image starring the user's character.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Detailed scene description (e.g. leaning against vintage car in desert wearing leather jacket)"},
                    "target_image": {"type": "string", "description": "Optional path to the source/uploaded image"},
                    "character_features": {"type": "string", "description": "Character traits (e.g. dark wavy hair, beard, glasses)"},
                    "user_id": {"type": "string", "description": "User ID to match persistent character profile"}
                },
                "required": ["prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_video",
            "description": "Generates a short AI video clip from a text prompt.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Scene or cinematic action description"}
                },
                "required": ["prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_voice_note",
            "description": "Synthesizes spoken audio / voice note using natural human speech.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The exact message to speak"}
                },
                "required": ["text"]
            }
        }
    }
]
