import asyncio
import base64
from datetime import datetime
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any, Dict, List, Optional
import uuid
import edge_tts
from core.config import DATA_DIR, settings
from tools.ffmpeg_utils import get_ffmpeg_path, get_audio_duration
from tools.style_templates import render_dynamic_canvas

logger = logging.getLogger(__name__)

OUTPUT_DIR = DATA_DIR / "generated_videos"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

async def build_viral_reel(
    product_name: str = "OpenTab",
    hook_title: str = "The Future of AI",
    tagline: str = "Autonomous intelligence for everyone.",
    old_label: str = "Manual Grunt Work",
    old_sub: str = "Wasted hours every day",
    new_label: str = "OpenTab Autopilot",
    new_sub: str = "100% Autonomous",
    stamp_text: str = "AI POWERED",
    script_text: str = "Stop doing manual work. OpenTab automates your marketing, channels, and life hands-free.",
    screenshot_path: Optional[str] = None,
    day_number: int = 1,
    progress_pct: int = 29,
    voice: str = "en-US-ChristopherNeural",
    theme: str = "dark_glass",
    accent_color: str = "#6366f1",
    features: Optional[List[Dict[str, str]]] = None,
    background_image_url: Optional[str] = None,
    progress_cb: Optional[Any] = None
) -> Dict[str, Any]:
    """Generates a complete 9:16 viral marketing reel in ANY style (dark_glass, cinematic, vibrant_pop, notebook)."""
    from playwright.async_api import async_playwright

    ffmpeg_bin = get_ffmpeg_path()
    temp_dir = Path(tempfile.mkdtemp(prefix="reel_build_"))
    audio_path = temp_dir / "voiceover.mp3"
    out_video = OUTPUT_DIR / f"reel_{uuid.uuid4().hex[:8]}.mp4"

    try:
        # Step 1: Synthesize Neural Voiceover
        logger.info(f"Synthesizing voiceover with voice '{voice}'...")
        if progress_cb:
            try:
                await progress_cb(f"🎙️ Synthesizing voiceover ({voice.split('-')[0].upper()})...")
            except Exception:
                pass

        communicate = edge_tts.Communicate(script_text, voice)
        await communicate.save(str(audio_path))

        # Get audio duration
        audio_duration = get_audio_duration(audio_path)
        logger.info(f"Audio duration: {audio_duration:.2f}s")

        # Step 2: Prepare Screen Content / Base64 image
        b64_img = None
        if screenshot_path and Path(screenshot_path).exists():
            with open(screenshot_path, "rb") as f:
                b64_img = base64.b64encode(f.read()).decode("utf-8")

        # Step 3: Render Dynamic HTML Canvas matching requested theme
        if not features:
            features = [
                {"title": new_label, "desc": new_sub, "icon": "🚀"},
                {"title": hook_title, "desc": tagline, "icon": "⚡"}
            ]

        html_rendered = render_dynamic_canvas(
            theme=theme,
            product_name=product_name,
            headline=hook_title,
            subtitle=tagline,
            tagline=tagline,
            stamp_text=stamp_text,
            highlight_pill=new_label,
            features=features,
            script_text=script_text,
            background_image_url=background_image_url,
            screenshot_b64=b64_img,
            accent_color=accent_color
        )

        # Step 4: High-Definition Snapshot Capture (Zero-OOM, <80MB RAM)
        logger.info("Capturing 9:16 high-definition scene snapshot with Playwright...")
        if progress_cb:
            try:
                await progress_cb("🎨 Composing 9:16 vertical motion scene...")
            except Exception:
                pass

        snapshot_path = temp_dir / "scene_snapshot.png"
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=settings.BROWSER_HEADLESS,
                args=[
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--no-first-run",
                    "--no-zygote",
                    "--renderer-process-limit=1",
                    "--disable-extensions",
                    "--disable-background-networking"
                ]
            )
            page = await browser.new_page(viewport={"width": 720, "height": 1280})
            await page.set_content(html_rendered, wait_until="domcontentloaded", timeout=8000)
            await page.wait_for_timeout(200)
            await page.screenshot(path=str(snapshot_path))
            await browser.close()

        # Step 5: Multiplex Audio and Kinetic Zoom Motion via FFmpeg
        logger.info("Muxing audio and kinetic zoom motion via FFmpeg...")
        if progress_cb:
            try:
                await progress_cb("🎬 Finalizing & encoding viral reel (sub-5s)...")
            except Exception:
                pass

        vf_filter = r"zoompan=z=min(zoom+0.0006\,1.04):d=125:x=iw/2-(iw/zoom/2):y=ih/2-(ih/zoom/2):s=720x1280:fps=24"
        final_cmd = [
            ffmpeg_bin, "-y",
            "-loop", "1",
            "-i", str(snapshot_path),
            "-i", str(audio_path),
            "-vf", vf_filter,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "fastdecode",
            "-threads", "1",
            "-crf", "24",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(out_video)
        ]
        res = subprocess.run(final_cmd, capture_output=True, text=True)
        if res.returncode != 0:
            logger.error(f"FFmpeg muxing error: {res.stderr}")
            raise RuntimeError(f"FFmpeg encoding failed: {res.stderr}")

        logger.info(f"Viral reel generated successfully: {out_video}")
        return {
            "status": "success",
            "video_path": str(out_video),
            "duration": audio_duration,
            "product_name": product_name,
            "hook": hook_title,
            "theme": theme
        }

    except Exception as e:
        logger.error(f"Failed to generate viral reel: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

VIRAL_REEL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "generate_viral_reel",
        "description": "Generates a complete 9:16 vertical viral marketing reel or video in ANY visual style (dark_glass, cinematic, vibrant_pop, notebook) with neural voiceover and subtitles.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {"type": "string", "description": "Product, brand, or topic name"},
                "hook_title": {"type": "string", "description": "Main catchy headline or hook question"},
                "tagline": {"type": "string", "description": "Supporting tagline or sub-headline"},
                "new_label": {"type": "string", "description": "Feature badge or primary highlight pill"},
                "stamp_text": {"type": "string", "description": "Badge/stamp callout (e.g. '100% PRIVATE', 'AI REVOLUTION', 'EXCLUSIVE')"},
                "script_text": {"type": "string", "description": "Concise spoken voiceover script (15-30 words, 8-12 seconds duration)"},
                "theme": {
                    "type": "string",
                    "enum": ["dark_glass", "cinematic", "vibrant_pop", "notebook"],
                    "description": "Visual style theme: 'dark_glass' (Apple/modern sleek tech), 'cinematic' (dramatic filmic storytelling), 'vibrant_pop' (colorful high-energy social), 'notebook' (build-in-public paper)"
                },
                "voice": {
                    "type": "string",
                    "description": "Neural voice: 'en-US-ChristopherNeural' (Deep tech/podcast), 'en-US-JennyNeural' (Female tech), 'en-US-GuyNeural' (Casual male), 'hi-IN-MadhurNeural' (Hindi male), 'hi-IN-SwaraNeural' (Hindi female), 'en-GB-RyanNeural' (British narrator)"
                },
                "accent_color": {"type": "string", "description": "Hex accent color for glows and badges (e.g. '#6366f1', '#10b981', '#ec4899', '#f59e0b')"}
            },
            "required": ["product_name", "hook_title", "script_text"]
        }
    }
}
