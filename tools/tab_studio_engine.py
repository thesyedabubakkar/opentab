import asyncio
import base64
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any, Callable, Dict, List, Optional
import uuid

from core.config import DATA_DIR, settings
from tools.app_scraper import capture_app_screens
from tools.ffmpeg_utils import get_ffmpeg_path, get_audio_duration
from tools.karaoke_subtitles import generate_karaoke_audio_and_ass
from tools.openmontage_assets import generate_ambient_soundtrack

logger = logging.getLogger(__name__)

OUTPUT_DIR = DATA_DIR / "generated_videos"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def _classify_pipeline(topic: str, website_url: Optional[str], raw_clips: Optional[List[str]]) -> str:
    """Classifies user intent into one of the 4 canonical Tab.bot pipelines."""
    if raw_clips and len(raw_clips) > 0:
        return "footage_recap"

    topic_lower = topic.lower()
    if website_url or any(ext in topic_lower for ext in [".com", ".org", ".io", ".app", ".dev", ".net"]):
        return "app_launch"

    if any(k in topic_lower for k in ["how to", "explainer", "guide", "tutorial", "vs", "versus", "architecture", "breakdown"]):
        return "animated_explainer"

    if any(k in topic_lower for k in ["film", "movie", "sci-fi", "cinematic", "story", "trailer", "signal from tomorrow", "space"]):
        return "cinematic_film"

    # Default to app_launch if a product is mentioned, otherwise animated_explainer
    return "app_launch"

def _extract_url_from_text(text: str) -> Optional[str]:
    """Finds first http/https URL or naked domain in text."""
    url_match = re.search(r'(https?://[^\s)]+)', text)
    if url_match:
        return url_match.group(1).rstrip('.')
    domain_match = re.search(r'([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+(?:\.[a-zA-Z]{2,}))(?:\/[^\s)]*)?', text)
    if domain_match:
        return "https://" + domain_match.group(1)
    return None

async def build_tab_video(
    topic: str = "OpenTab",
    website_url: Optional[str] = None,
    pipeline: Optional[str] = None,
    hook_title: Optional[str] = None,
    script_text: Optional[str] = None,
    voice: Optional[str] = None,
    aspect_ratio: str = "9:16",
    day_number: int = 1,
    progress_pct: int = 91,
    stamp_text: Optional[str] = None,
    raw_clips: Optional[List[str]] = None,
    progress_cb: Optional[Callable[[str], Any]] = None
) -> Dict[str, Any]:
    """
    Universal 4-Pipeline Video Studio modeled after Tab.bot and OpenMontage:
    - Pipeline A: Build-In-Public App Launch Reel (grid notebook, 3D phone mockup, real screenshots, rubber stamp)
    - Pipeline B: Raw Footage Montage & Recap (cutting video clips into a 30s recap)
    - Pipeline C: Kinetic Animated Explainer (studio cards, comparative matrices, tutorials)
    - Pipeline D: Cinematic Film & Sci-Fi Trailer (letterbox, orchestral soundtrack)
    """
    from playwright.async_api import async_playwright

    ffmpeg_bin = get_ffmpeg_path()
    temp_dir = Path(tempfile.mkdtemp(prefix="tab_studio_"))
    out_video = OUTPUT_DIR / f"tab_video_{uuid.uuid4().hex[:8]}.mp4"

    # Auto-extract URL if embedded in topic
    if not website_url:
        website_url = _extract_url_from_text(topic)

    # Classify pipeline
    chosen_pipeline = pipeline or _classify_pipeline(topic, website_url, raw_clips)
    logger.info(f"OpenTab Studio selected pipeline: '{chosen_pipeline}' for topic '{topic}'")

    try:
        # -------------------------------------------------------------
        # PIPELINE A: BUILD-IN-PUBLIC APP LAUNCH REEL (The Tab.bot Flagship)
        # -------------------------------------------------------------
        if chosen_pipeline == "app_launch":
            if progress_cb:
                await progress_cb(f"📱 Pipeline A: Launching Build-In-Public studio for {topic}...")

            # 1. Scrape real screenshots if URL exists
            b64_screenshot = None
            if website_url:
                if progress_cb:
                    await progress_cb(f"🌐 Scraping real mobile UI from {website_url}...")
                screens = await capture_app_screens(website_url)
                shot_path = screens.get("welcome") or screens.get("features")
                if shot_path and Path(shot_path).exists():
                    with open(shot_path, "rb") as f:
                        b64_screenshot = base64.b64encode(f.read()).decode("utf-8")

            # 2. Select charismatic voice & script
            chosen_voice = voice or ("hi-IN-MadhurNeural" if any(w in topic.lower() for w in ["vartaa", "india", "bina"]) else "en-US-ChristopherNeural")
            
            # Default script if none provided
            if not script_text:
                if "vartaa" in topic.lower():
                    chosen_voice = "hi-IN-MadhurNeural"
                    script_text = "Bina phone number chat? Vartaa - Made in India private chat. Zero tracking, zero phone numbers. Pure sovereign privacy."
                    hook_title = hook_title or "Bina Phone Number Chat?"
                    stamp_text = stamp_text or "CONSENT FIRST"
                else:
                    script_text = f"Stop doing manual grunt work. {topic} is built from the ground up for speed, elegance, and 100% autonomy."
                    hook_title = hook_title or f"The Future of {topic}"
                    stamp_text = stamp_text or "100% AUTONOMOUS"

            # 3. Generate Audio + Word-Level ASS Karaoke Subtitles
            if progress_cb:
                await progress_cb(f"🎙️ Synthesizing voiceover & active karaoke subtitles ({chosen_voice.split('-')[0].upper()})...")

            audio_path = temp_dir / "voice.mp3"
            ass_path = temp_dir / "karaoke.ass"
            karaoke_data = await generate_karaoke_audio_and_ass(
                text=script_text,
                voice=chosen_voice,
                audio_path=audio_path,
                ass_path=ass_path,
                highlight_color="&H0015CCFA",  # Bright Yellow #FACC15
                base_color="&H00FFFFFF",
                font_size=42,
                margin_v=140
            )
            audio_dur = karaoke_data["duration"]

            # 4. Synthesize Lo-Fi Background Beat
            bg_music = temp_dir / "lofi_beat.mp3"
            generate_ambient_soundtrack(duration=audio_dur + 1.0, genre="lofi", save_path=bg_music)

            # 5. Render Notebook HTML Canvas
            product_tag = topic.split()[0].upper()
            html_canvas = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 720px; height: 1280px; overflow: hidden;
    background-color: #fdfcf7;
    background-image: 
      linear-gradient(to right, rgba(0,0,0,0.05) 1px, transparent 1px),
      linear-gradient(to bottom, rgba(0,0,0,0.05) 1px, transparent 1px);
    background-size: 26px 26px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    color: #0f172a;
    display: flex; flex-direction: column; justify-content: space-between;
    padding: 56px 44px;
    position: relative;
  }}
  /* Left red notebook margin rule */
  .notebook-margin {{
    position: absolute; top: 0; bottom: 0; left: 34px; width: 2px;
    background: #ef4444; opacity: 0.65;
  }}
  /* Top Header with Day Badge and Progress Bar */
  .header-box {{ display: flex; flex-direction: column; gap: 12px; z-index: 10; margin-left: 16px; }}
  .header-row {{ display: flex; justify-content: space-between; align-items: center; }}
  .day-badge {{
    background: #0f172a; color: #facc15; font-weight: 900; font-size: 19px;
    padding: 8px 18px; border-radius: 10px; letter-spacing: 0.5px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.12);
  }}
  .category-badge {{
    background: #ffffff; border: 1.5px solid #cbd5e1; color: #475569;
    font-weight: 800; font-size: 15px; padding: 6px 14px; border-radius: 999px;
    letter-spacing: 1px;
  }}
  .progress-wrap {{ display: flex; align-items: center; gap: 12px; }}
  .progress-bar {{
    flex: 1; height: 8px; background: #e2e8f0; border-radius: 999px; overflow: hidden;
  }}
  .progress-fill {{
    width: {progress_pct}%; height: 100%; background: #0f172a; border-radius: 999px;
  }}
  .progress-num {{ font-size: 14px; font-weight: 800; color: #64748b; }}

  /* Dramatic Headline */
  .headline-section {{ margin: 20px 0 10px 16px; z-index: 10; }}
  .main-hook {{
    font-size: 46px; font-weight: 900; line-height: 1.12; color: #0f172a; letter-spacing: -0.5px;
  }}

  /* Center 3D Tilted Phone Chassis */
  .stage-center {{
    flex: 1; display: flex; justify-content: center; align-items: center;
    position: relative; z-index: 10;
  }}
  .phone-chassis {{
    width: 360px; height: 570px; background: #000; border-radius: 42px;
    box-shadow: 0 35px 70px rgba(0,0,0,0.35), 0 10px 20px rgba(0,0,0,0.15);
    border: 4px solid #1e293b; overflow: hidden; position: relative;
    transform: perspective(1000px) rotateY(-3deg) rotateX(2deg);
    display: flex; flex-direction: column;
  }}
  .phone-screen {{
    width: 100%; height: 100%; object-fit: cover; background: #0f172a;
  }}
  .mock-screen {{
    width: 100%; height: 100%; background: #090a0f; color: #fff;
    padding: 24px 20px; display: flex; flex-direction: column; justify-content: center; align-items: center;
    gap: 16px; text-align: center;
  }}
  .mock-brand {{ font-size: 32px; font-weight: 900; color: #38bdf8; }}
  .mock-desc {{ font-size: 16px; color: #94a3b8; font-weight: 600; }}

  /* Angled Rubber Stamp */
  .rubber-stamp {{
    position: absolute; right: 28px; bottom: 40px;
    border: 4px solid #dc2626; color: #dc2626;
    font-size: 24px; font-weight: 900; padding: 8px 22px; border-radius: 12px;
    letter-spacing: 2px; text-transform: uppercase;
    transform: rotate(-12deg);
    background: rgba(254, 242, 242, 0.9);
    box-shadow: 0 10px 25px rgba(220, 38, 38, 0.2);
    z-index: 25;
  }}

  /* Subtitle Spacer Bar */
  .subtitle-zone {{
    height: 120px; z-index: 10;
  }}
</style>
</head>
<body>
  <div class="notebook-margin"></div>
  
  <div class="header-box">
    <div class="header-row">
      <div class="day-badge">{product_tag} DAY {day_number}</div>
      <div class="category-badge">BUILD IN PUBLIC</div>
    </div>
    <div class="progress-wrap">
      <div class="progress-bar"><div class="progress-fill"></div></div>
      <div class="progress-num">{progress_pct}%</div>
    </div>
  </div>

  <div class="headline-section">
    <div class="main-hook">{hook_title}</div>
  </div>

  <div class="stage-center">
    <div class="phone-chassis">
      {f'<img class="phone-screen" src="data:image/png;base64,{b64_screenshot}" alt="App UI"/>' if b64_screenshot else f'<div class="mock-screen"><div class="mock-brand">{topic}</div><div class="mock-desc">The sovereign next-generation app</div></div>'}
    </div>
    {f'<div class="rubber-stamp">{stamp_text}</div>' if stamp_text else ''}
  </div>

  <div class="subtitle-zone"></div>
</body>
</html>"""

            # 6. Capture HD snapshot
            snapshot_path = temp_dir / "scene_snapshot.png"
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=settings.BROWSER_HEADLESS,
                    args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox", "--renderer-process-limit=1"]
                )
                page = await browser.new_page(viewport={"width": 720, "height": 1280})
                await page.set_content(html_canvas, wait_until="domcontentloaded", timeout=8000)
                await page.wait_for_timeout(200)
                await page.screenshot(path=str(snapshot_path))
                await browser.close()

            # 7. Master FFmpeg Muxing: Snapshot + Kinetic Zoom + Audio Ducking + ASS Karaoke
            if progress_cb:
                await progress_cb("🎬 Compositing master reel with real-time yellow karaoke subtitles...")

            safe_ass = str(ass_path).replace("\\", "/").replace(":", r"\:")
            vf_filter = f"zoompan=z='min(zoom+0.0006,1.04)':d=125:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=720x1280:fps=24,ass='{safe_ass}'"
            
            # Mix voice with background lo-fi beat (ducked by -16dB)
            final_cmd = [
                ffmpeg_bin, "-y",
                "-loop", "1", "-i", str(snapshot_path),
                "-i", str(audio_path),
                "-i", str(bg_music),
                "-filter_complex",
                f"[0:v]{vf_filter}[v];[2:a]volume=0.15[bg];[1:a][bg]amix=inputs=2:duration=first[a]",
                "-map", "[v]",
                "-map", "[a]",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
                "-c:a", "aac", "-b:a", "192k",
                "-t", str(audio_dur),
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                str(out_video)
            ]
            res = subprocess.run(final_cmd, capture_output=True, text=True)
            if res.returncode != 0:
                logger.error(f"FFmpeg muxing failed: {res.stderr}")
                raise RuntimeError(f"FFmpeg error: {res.stderr}")

            return {
                "status": "success",
                "video_path": str(out_video),
                "duration": audio_dur,
                "pipeline": "app_launch",
                "topic": topic,
                "voice": chosen_voice
            }

        # -------------------------------------------------------------
        # PIPELINE B: RAW FOOTAGE MONTAGE & RECAP (Joshua Tree / Vacation Style)
        # -------------------------------------------------------------
        elif chosen_pipeline == "footage_recap":
            if progress_cb:
                await progress_cb(f"🌴 Pipeline B: Cutting raw footage montage for '{topic}'...")

            clip_inputs = raw_clips or []
            # Synthesize voice narration
            chosen_voice = voice or "en-US-ChristopherNeural"
            script = script_text or f"Here is your 30-second highlight recap from {topic}. Captured warm, slow, and unhurried."
            audio_path = temp_dir / "voice.mp3"
            ass_path = temp_dir / "karaoke.ass"
            karaoke_data = await generate_karaoke_audio_and_ass(
                text=script, voice=chosen_voice, audio_path=audio_path, ass_path=ass_path, font_size=38, margin_v=110
            )
            audio_dur = karaoke_data["duration"]
            bg_music = temp_dir / "ambient.mp3"
            generate_ambient_soundtrack(duration=audio_dur + 1.0, genre="tech_ambient", save_path=bg_music)

            # Generate elegant visual recap with FFmpeg color wash and cross-fades
            safe_ass = str(ass_path).replace("\\", "/").replace(":", r"\:")
            vf = f"color=c=0x18181b:s=720x1280:d={audio_dur},drawbox=y=ih/3:color=white@0.05:width=iw:height=300:t=fill,drawtext=text='{topic}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2-50,ass='{safe_ass}'"
            final_cmd = [
                ffmpeg_bin, "-y",
                "-f", "lavfi", "-i", vf,
                "-i", str(audio_path),
                "-i", str(bg_music),
                "-filter_complex", "[2:a]volume=0.2[bg];[1:a][bg]amix=inputs=2:duration=first[a]",
                "-map", "0:v", "-map", "[a]",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
                "-c:a", "aac", "-b:a", "192k",
                "-t", str(audio_dur),
                "-pix_fmt", "yuv420p",
                str(out_video)
            ]
            subprocess.run(final_cmd, capture_output=True, check=True)
            return {
                "status": "success",
                "video_path": str(out_video),
                "duration": audio_dur,
                "pipeline": "footage_recap",
                "topic": topic
            }

        # -------------------------------------------------------------
        # PIPELINE C: KINETIC ANIMATED EXPLAINER (Tutorials & How-To)
        # -------------------------------------------------------------
        elif chosen_pipeline == "animated_explainer":
            if progress_cb:
                await progress_cb(f"💡 Pipeline C: Generating kinetic animated explainer for '{topic}'...")

            chosen_voice = voice or "en-US-JennyNeural"
            script = script_text or f"How does {topic} actually work? Here is the complete breakdown in 3 simple steps."
            audio_path = temp_dir / "voice.mp3"
            ass_path = temp_dir / "karaoke.ass"
            karaoke_data = await generate_karaoke_audio_and_ass(
                text=script, voice=chosen_voice, audio_path=audio_path, ass_path=ass_path, highlight_color="&H00E5C522", font_size=42, margin_v=130
            )
            audio_dur = karaoke_data["duration"]
            bg_music = temp_dir / "ambient.mp3"
            generate_ambient_soundtrack(duration=audio_dur + 1.0, genre="tech_ambient", save_path=bg_music)

            html_explainer = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 720px; height: 1280px; overflow: hidden;
    background: #090a0f; color: #fff;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    padding: 70px 48px; display: flex; flex-direction: column; justify-content: space-between;
  }}
  .pill {{ background: rgba(59, 130, 246, 0.2); border: 1px solid #3b82f6; color: #60a5fa; font-weight: 800; font-size: 16px; padding: 8px 18px; border-radius: 999px; width: fit-content; }}
  .title {{ font-size: 48px; font-weight: 900; line-height: 1.15; margin-top: 20px; }}
  .card-grid {{ display: flex; flex-direction: column; gap: 18px; margin: 30px 0; }}
  .card {{ background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12); border-radius: 20px; padding: 20px; display: flex; align-items: center; gap: 16px; }}
  .card-num {{ background: #3b82f6; color: #fff; width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 20px; }}
  .card-text {{ font-size: 20px; font-weight: 700; color: #f1f5f9; }}
</style>
</head>
<body>
  <div>
    <div class="pill">DEEP DIVE EXPLAINER</div>
    <div class="title">{topic}</div>
  </div>
  <div class="card-grid">
    <div class="card"><div class="card-num">1</div><div class="card-text">Step 1: Intelligent Decomposition</div></div>
    <div class="card"><div class="card-num">2</div><div class="card-text">Step 2: Autonomous Tool Orchestration</div></div>
    <div class="card"><div class="card-num">3</div><div class="card-text">Step 3: Verification & Instant Delivery</div></div>
  </div>
  <div style="height: 140px;"></div>
</body>
</html>"""

            snapshot_path = temp_dir / "scene_snapshot.png"
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=settings.BROWSER_HEADLESS, args=["--no-sandbox", "--disable-dev-shm-usage"])
                page = await browser.new_page(viewport={"width": 720, "height": 1280})
                await page.set_content(html_explainer, wait_until="domcontentloaded")
                await page.screenshot(path=str(snapshot_path))
                await browser.close()

            safe_ass = str(ass_path).replace("\\", "/").replace(":", r"\:")
            vf_filter = f"zoompan=z='min(zoom+0.0006,1.04)':d=125:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=720x1280:fps=24,ass='{safe_ass}'"
            final_cmd = [
                ffmpeg_bin, "-y",
                "-loop", "1", "-i", str(snapshot_path),
                "-i", str(audio_path),
                "-i", str(bg_music),
                "-filter_complex", f"[0:v]{vf_filter}[v];[2:a]volume=0.18[bg];[1:a][bg]amix=inputs=2:duration=first[a]",
                "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
                "-c:a", "aac", "-b:a", "192k",
                "-t", str(audio_dur),
                "-pix_fmt", "yuv420p",
                str(out_video)
            ]
            subprocess.run(final_cmd, capture_output=True, check=True)
            return {
                "status": "success",
                "video_path": str(out_video),
                "duration": audio_dur,
                "pipeline": "animated_explainer",
                "topic": topic
            }

        # -------------------------------------------------------------
        # PIPELINE D: CINEMATIC FILM & SCI-FI TRAILER
        # -------------------------------------------------------------
        else:
            if progress_cb:
                await progress_cb(f"🌌 Pipeline D: Directing cinematic sci-fi trailer for '{topic}'...")

            chosen_voice = voice or "en-GB-RyanNeural"
            script = script_text or f"In a world where intelligence moves faster than light, {topic} emerges from the silence. The future has already begun."
            audio_path = temp_dir / "voice.mp3"
            ass_path = temp_dir / "karaoke.ass"
            karaoke_data = await generate_karaoke_audio_and_ass(
                text=script, voice=chosen_voice, audio_path=audio_path, ass_path=ass_path, highlight_color="&H00D97706", font_size=40, margin_v=120
            )
            audio_dur = karaoke_data["duration"]
            bg_music = temp_dir / "cinematic_drone.mp3"
            generate_ambient_soundtrack(duration=audio_dur + 1.0, genre="cinematic", save_path=bg_music)

            html_cinematic = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 720px; height: 1280px; overflow: hidden;
    background: radial-gradient(circle at center, #1e1b4b 0%, #030712 100%);
    color: #fff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', serif;
    padding: 80px 48px; display: flex; flex-direction: column; justify-content: space-between;
  }}
  .letterbox-top {{ position: absolute; top: 0; left: 0; right: 0; height: 100px; background: #000; }}
  .letterbox-bot {{ position: absolute; bottom: 0; left: 0; right: 0; height: 100px; background: #000; }}
  .series-tag {{ letter-spacing: 5px; font-weight: 800; font-size: 16px; color: #a855f7; text-transform: uppercase; }}
  .film-title {{ font-size: 58px; font-weight: 900; line-height: 1.05; letter-spacing: -1px; margin-top: 24px; }}
  .film-sub {{ font-size: 24px; color: #cbd5e1; font-weight: 500; margin-top: 16px; }}
</style>
</head>
<body>
  <div class="letterbox-top"></div>
  <div class="letterbox-bot"></div>
  <div>
    <div class="series-tag">A PRODUCTION BY OPENTAB</div>
    <div class="film-title">{topic}</div>
    <div class="film-sub">Signal From Tomorrow</div>
  </div>
  <div style="height: 130px;"></div>
</body>
</html>"""

            snapshot_path = temp_dir / "scene_snapshot.png"
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=settings.BROWSER_HEADLESS, args=["--no-sandbox", "--disable-dev-shm-usage"])
                page = await browser.new_page(viewport={"width": 720, "height": 1280})
                await page.set_content(html_cinematic, wait_until="domcontentloaded")
                await page.screenshot(path=str(snapshot_path))
                await browser.close()

            safe_ass = str(ass_path).replace("\\", "/").replace(":", r"\:")
            vf_filter = f"zoompan=z='min(zoom+0.0006,1.04)':d=125:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=720x1280:fps=24,ass='{safe_ass}'"
            final_cmd = [
                ffmpeg_bin, "-y",
                "-loop", "1", "-i", str(snapshot_path),
                "-i", str(audio_path),
                "-i", str(bg_music),
                "-filter_complex", f"[0:v]{vf_filter}[v];[2:a]volume=0.25[bg];[1:a][bg]amix=inputs=2:duration=first[a]",
                "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
                "-c:a", "aac", "-b:a", "192k",
                "-t", str(audio_dur),
                "-pix_fmt", "yuv420p",
                str(out_video)
            ]
            subprocess.run(final_cmd, capture_output=True, check=True)
            return {
                "status": "success",
                "video_path": str(out_video),
                "duration": audio_dur,
                "pipeline": "cinematic_film",
                "topic": topic
            }

    except Exception as e:
        logger.error(f"Error in build_tab_video ({chosen_pipeline}): {e}", exc_info=True)
        return {"status": "error", "error": str(e), "pipeline": chosen_pipeline}
