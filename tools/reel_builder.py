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

logger = logging.getLogger(__name__)

TEMPLATE_PATH = Path(__file__).parent / "reel_templates" / "vartaa_canvas.html"
OUTPUT_DIR = DATA_DIR / "generated_videos"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

async def build_viral_reel(
    product_name: str = "VARTAA",
    hook_title: str = "Bina phone number chat?",
    tagline: str = "Privacy ab wapas aayegi.",
    old_label: str = "+91 98XXX Phone OTP",
    old_sub: str = "Data leak risk",
    new_label: str = "@username",
    new_sub: str = "100% Private",
    stamp_text: str = "NO PHONE · NO OTP",
    script_text: str = "Phone number se sign up karke privacy ka tamasha khatam. Ab sirf username se connect karo.",
    screenshot_path: Optional[str] = None,
    day_number: int = 1,
    progress_pct: int = 29,
    voice: str = "hi-IN-MadhurNeural",
    progress_cb: Optional[Any] = None
) -> Dict[str, Any]:
    """Generates a complete 9:16 viral marketing reel with 3D phone mockup and voiceover."""
    from playwright.async_api import async_playwright

    ffmpeg_bin = get_ffmpeg_path()
    temp_dir = Path(tempfile.mkdtemp(prefix="reel_build_"))
    audio_path = temp_dir / "voiceover.mp3"
    temp_html_path = temp_dir / "canvas.html"
    out_video = OUTPUT_DIR / f"reel_{uuid.uuid4().hex[:8]}.mp4"

    try:
        # Step 1: Synthesize Neural Voiceover
        logger.info(f"Synthesizing voiceover with voice '{voice}'...")
        communicate = edge_tts.Communicate(script_text, voice)
        await communicate.save(str(audio_path))

        # Get audio duration
        audio_duration = get_audio_duration(audio_path)
        logger.info(f"Audio duration: {audio_duration:.2f}s")

        # Step 2: Prepare Screen Content (User Screenshot or Synthetic Dark UI)
        if screenshot_path and Path(screenshot_path).exists():
            with open(screenshot_path, "rb") as f:
                b64_img = base64.b64encode(f.read()).decode("utf-8")
            screen_body = f'<img class="screen-img" src="data:image/jpeg;base64,{b64_img}" alt="App Screen" />'
        else:
            screen_body = f"""
            <div class="app-header">
              <div class="app-brand">{product_name}</div>
              <div class="app-step">Step 1 of 4</div>
            </div>
            <div class="screen-body">
              <div class="ui-badge-pill">☑️ Zero OTP Identity</div>
              <div class="ui-card">
                <div class="ui-title">Choose your @username</div>
                <div class="ui-desc">Your conversations. Your identity. No phone numbers exposed to strangers.</div>
              </div>
              <div class="ui-card" style="border-color: #10b981;">
                <div class="ui-title" style="color: #34d399;">Consent-First Connections</div>
                <div class="ui-desc">Strangers cannot message you directly. Real privacy restored.</div>
              </div>
            </div>
            """

        # Prepare Kinetic Subtitles
        # Wrap middle word or key phrase in highlight pill
        words = script_text.split()
        if len(words) >= 4:
            mid = len(words) // 2
            highlighted = f"{' '.join(words[:mid-1])} <span class=\"sub-highlight\">{' '.join(words[mid-1:mid+2])}</span> {' '.join(words[mid+2:])}"
        else:
            highlighted = f"<span class=\"sub-highlight\">{script_text}</span>"

        # Step 3: Populate Template
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            template_content = f.read()

        html_rendered = template_content \
            .replace("{{PRODUCT_NAME}}", product_name) \
            .replace("{{DAY_NUMBER}}", str(day_number)) \
            .replace("{{DATE_TEXT}}", datetime.now().strftime("%d %b %Y").upper()) \
            .replace("{{SUB_BADGE}}", "BUILD IN PUBLIC") \
            .replace("{{PROGRESS_PCT}}", str(progress_pct)) \
            .replace("{{HOOK_PILL}}", hook_title) \
            .replace("{{TAGLINE}}", tagline) \
            .replace("{{OLD_LABEL}}", old_label) \
            .replace("{{OLD_SUB}}", old_sub) \
            .replace("{{NEW_LABEL}}", new_label) \
            .replace("{{NEW_SUB}}", new_sub) \
            .replace("{{STAMP_TEXT}}", stamp_text) \
            .replace("{{SCREEN_BODY}}", screen_body) \
            .replace("{{SUBTITLE_HTML}}", highlighted)

        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(html_rendered)

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
            # Fallback copy
            shutil.copy(raw_video_path, out_video)

        logger.info(f"Viral reel generated successfully: {out_video}")
        return {
            "status": "success",
            "video_path": str(out_video),
            "duration": audio_duration,
            "product_name": product_name,
            "hook": hook_title
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
        "description": "Generates a complete 9:16 vertical viral marketing reel video featuring dynamic phone mockups, comparison badges, and kinetic subtitles.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {"type": "string", "description": "Product or app name (e.g. 'VARTAA', 'OFFLO')"},
                "hook_title": {"type": "string", "description": "POV hook or question (e.g. 'Bina phone number chat?')"},
                "tagline": {"type": "string", "description": "Supporting tagline (e.g. 'Privacy ab wapas aayegi')"},
                "old_label": {"type": "string", "description": "Old way with red cross (e.g. '+91 98XXX Phone OTP')"},
                "new_label": {"type": "string", "description": "New way with green check (e.g. '@username')"},
                "stamp_text": {"type": "string", "description": "Angled rubber stamp text (e.g. 'NO PHONE · NO OTP')"},
                "script_text": {"type": "string", "description": "Full narration script spoken by the neural voiceover"},
                "voice": {"type": "string", "description": "Voice identifier (e.g. 'hi-IN-MadhurNeural', 'en-US-ChristopherNeural', 'kn-IN-GaganNeural')"}
            },
            "required": ["product_name", "hook_title", "script_text"]
        }
    }
}
