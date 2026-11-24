import asyncio
import base64
import logging
from pathlib import Path
import subprocess
from typing import Any, Dict, List, Optional
import urllib.parse
import uuid
import httpx
from core.config import DATA_DIR, settings
from tools.ffmpeg_utils import get_ffmpeg_path

logger = logging.getLogger(__name__)

MEDIA_DIR = DATA_DIR / "higgsfield_media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

class OpenHiggsfieldClient:
    """
    Client for Open-Higgsfield (modeled after wide-trace/open-higgsfield).
    Connects to multi-model AI video/image generation providers:
    - Higgsfield Platform API (Wan 2.1, Kling, LTX, MiniMax, Flux) if configured
    - Zero-cost open fallback via Pollinations AI & procedural canvas
    """
    def __init__(self):
        self.api_key = settings.HIGGSFIELD_API_KEY
        self.base_url = "https://api.higgsfield.ai/v1"

    async def generate_media(
        self,
        prompt: str,
        media_type: str = "image", # "image" or "video"
        model: Optional[str] = None,
        aspect_ratio: str = "16:9",
        save_path: Optional[Path] = None
    ) -> Path:
        """Generates AI media (image or video) tailored to the prompt."""
        if not save_path:
            ext = "mp4" if media_type == "video" else "jpg"
            save_path = MEDIA_DIR / f"hf_{uuid.uuid4().hex[:8]}.{ext}"

        # 1. If Higgsfield API key is provided, use official endpoint
        if self.api_key and ":" in self.api_key:
            try:
                res = await self._call_higgsfield_api(prompt, media_type, model, aspect_ratio, save_path)
                if res and res.exists():
                    return res
            except Exception as e:
                logger.warning(f"Higgsfield API call failed ({e}), falling back to open models.")

        # 2. Free Open-Source Multi-Model Fallback
        return await self._generate_free_fallback(prompt, media_type, aspect_ratio, save_path)

    async def _call_higgsfield_api(
        self,
        prompt: str,
        media_type: str,
        model: Optional[str],
        aspect_ratio: str,
        save_path: Path
    ) -> Optional[Path]:
        """Calls Higgsfield multi-model API using KEY_ID:SECRET credentials."""
        target_model = model or ("wan-2.1" if media_type == "video" else "flux-schnell")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": target_model,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "duration": 3.0 if media_type == "video" else None
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(f"{self.base_url}/generate", headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                media_url = data.get("media_url") or data.get("url")
                if media_url:
                    m_resp = await client.get(media_url)
                    with open(save_path, "wb") as f:
                        f.write(m_resp.content)
                    return save_path
        return None

    async def _generate_free_fallback(
        self,
        prompt: str,
        media_type: str,
        aspect_ratio: str,
        save_path: Path
    ) -> Path:
        """Generates high-quality media using free Pollinations & FFmpeg canvas."""
        width, height = (800, 450) if aspect_ratio == "16:9" else (720, 1280)
        encoded_prompt = urllib.parse.quote(prompt.strip())
        poll_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&seed={uuid.uuid4().int % 100000}"

        img_path = save_path if media_type == "image" else MEDIA_DIR / f"temp_{uuid.uuid4().hex[:8]}.jpg"
        
        # Download image from Pollinations with retry
        downloaded = False
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                    resp = await client.get(poll_url)
                    if resp.status_code == 200:
                        with open(img_path, "wb") as f:
                            f.write(resp.content)
                        downloaded = True
                        break
            except Exception:
                await asyncio.sleep(2.0)

        # Fallback to local colored canvas with text overlay if network is down
        ffmpeg = get_ffmpeg_path()
        if not downloaded:
            safe_text = prompt[:30].replace("'", "").replace(":", " ")
            cmd = [
                ffmpeg, "-y", "-nostdin",
                "-f", "lavfi", "-i", f"color=c=0x0f172a:s={width}x{height}:d=1",
                "-vf", f"drawtext=text='{safe_text}':fontcolor=white:fontsize=28:x=(w-text_w)/2:y=(h-text_h)/2",
                "-vframes", "1",
                str(img_path)
            ]
            await asyncio.to_thread(subprocess.run, cmd, capture_output=True)

        if media_type == "image":
            return img_path

        # If video is requested, convert image to subtle 3-second animated zoom video
        cmd_vid = [
            ffmpeg, "-y", "-nostdin",
            "-loop", "1", "-i", str(img_path),
            "-vf", "zoompan=z='min(zoom+0.0015,1.15)':d=90:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=800x450:fps=30",
            "-t", "3",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            str(save_path)
        ]
        await asyncio.to_thread(subprocess.run, cmd_vid, capture_output=True)
        return save_path
