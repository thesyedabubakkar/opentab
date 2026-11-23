import asyncio
import logging
from pathlib import Path
import subprocess
from typing import Any, Dict, List, Optional, Tuple
import urllib.parse
import uuid
import edge_tts
import httpx
from core.config import DATA_DIR
from tools.ffmpeg_utils import get_ffmpeg_path, get_audio_duration

logger = logging.getLogger(__name__)

ASSETS_DIR = DATA_DIR / "montage_assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

async def fetch_scene_visual(
    visual_prompt: str,
    aspect_ratio: str = "9:16",
    save_path: Optional[Path] = None
) -> Path:
    """Generates an AI visual asset for a specific scene."""
    if aspect_ratio == "9:16":
        width, height = 720, 1280
    else:
        width, height = 1280, 720

    if not save_path:
        save_path = ASSETS_DIR / f"vis_{uuid.uuid4().hex[:8]}.jpg"

    encoded = urllib.parse.quote(visual_prompt.strip())
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true&seed={uuid.uuid4().int % 100000}"

    logger.info(f"Generating visual asset for prompt: '{visual_prompt[:60]}...'")
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=45.0, follow_redirects=True) as client:
                resp = await client.get(url)
                if resp.status_code in (402, 429) and attempt == 0:
                    logger.warning("Pollinations rate limit hit. Waiting 5.5s before retry...")
                    await asyncio.sleep(5.5)
                    continue
                resp.raise_for_status()
                with open(save_path, "wb") as f:
                    f.write(resp.content)
                return save_path
        except Exception as e:
            if attempt == 0:
                await asyncio.sleep(5.5)
                continue
            logger.warning(f"Could not download AI image from Pollinations: {e}. Generating placeholder visual.")
            break

    # Fallback to local colored canvas with FFmpeg if network fails
    ffmpeg = get_ffmpeg_path()
    subprocess.run([
        ffmpeg, "-y",
        "-f", "lavfi", "-i", f"color=c=0x111827:s={width}x{height}:d=1",
        "-vframes", "1",
        str(save_path)
    ], capture_output=True)
    return save_path

async def synthesize_scene_voice(
    text: str,
    voice: str = "en-US-ChristopherNeural",
    save_path: Optional[Path] = None
) -> Tuple[Path, float]:
    """Synthesizes neural voiceover for a single scene and returns (audio_path, duration)."""
    if not save_path:
        save_path = ASSETS_DIR / f"voice_{uuid.uuid4().hex[:8]}.mp3"

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(save_path))

    duration = get_audio_duration(save_path)
    # Ensure minimum 2.5s duration
    if duration < 2.5:
        duration = 2.5
    return save_path, duration

def generate_ambient_soundtrack(
    duration: float,
    genre: str = "tech_ambient",
    save_path: Optional[Path] = None
) -> Path:
    """Generates a subtle, royalty-free ambient synth or lo-fi soundtrack using FFmpeg audio synthesizer."""
    if not save_path:
        save_path = ASSETS_DIR / f"music_{uuid.uuid4().hex[:8]}.mp3"

    ffmpeg = get_ffmpeg_path()

    # Different frequency recipes for genres
    if genre == "cinematic":
        # Deep cinematic drone
        expr = "0.12*sin(2*PI*55*t)+0.08*sin(2*PI*110*t)+0.05*sin(2*PI*164.81*t)+0.03*sin(2*PI*220*t)"
    elif genre == "lofi":
        # Warm relaxed chord
        expr = "0.1*sin(2*PI*174.61*t)+0.08*sin(2*PI*220*t)+0.07*sin(2*PI*261.63*t)+0.05*sin(2*PI*329.63*t)"
    else:
        # Tech ambient pulsing chord (A minor 7th)
        expr = "0.09*sin(2*PI*110*t)+0.07*sin(2*PI*130.81*t)+0.06*sin(2*PI*164.81*t)+0.04*sin(2*PI*196*t)"

    cmd = [
        ffmpeg, "-y",
        "-f", "lavfi",
        "-i", f"aevalsrc={expr}:s=44100:d={duration+2}",
        "-af", f"afade=t=in:ss=0:d=1,afade=t=out:st={duration}:d=2",
        "-c:a", "mp3", "-b:a", "128k",
        str(save_path)
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return save_path
