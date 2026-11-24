import asyncio
import base64
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any, Callable, Dict, List, Optional, Tuple
import uuid

from core.config import DATA_DIR, settings
from core.prompt2video_director import Prompt2VideoDirector
from tools.app_scraper import capture_app_screens
from tools.dynamic_scene_renderer import render_scene_html
from tools.ffmpeg_utils import get_ffmpeg_path, get_audio_duration
from tools.higgsfield_client import OpenHiggsfieldClient
from tools.karaoke_subtitles import generate_karaoke_audio_and_ass, _format_ass_time
from tools.openmontage_assets import generate_ambient_soundtrack

logger = logging.getLogger(__name__)

OUTPUT_DIR = DATA_DIR / "generated_videos"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def _classify_pipeline(topic: str, website_url: Optional[str] = None, raw_clips: Optional[List[str]] = None) -> str:
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

def _get_base_html(header_day: str, progress_pct: str, date_text: str, content_html: str) -> str:
    """Generates standard notebook paper page matching Tab.bot's signature aesthetic."""
    return f"""<!DOCTYPE html>
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
  /* Left red notebook margin line */
  .notebook-margin {{
    position: absolute; top: 0; bottom: 0; left: 34px; width: 2px;
    background: #ef4444; opacity: 0.7;
  }}
  /* Header Section */
  .header-box {{ display: flex; flex-direction: column; gap: 10px; z-index: 10; margin-left: 18px; }}
  .header-row {{ display: flex; justify-content: space-between; align-items: center; }}
  .day-badge {{
    background: #0f172a; color: #fff; font-weight: 900; font-size: 19px;
    padding: 7px 18px; border-radius: 9px; letter-spacing: 0.5px;
  }}
  .day-highlight {{ color: #facc15; margin-left: 6px; }}
  .header-meta {{
    font-size: 14px; font-weight: 800; text-align: right; color: #64748b; line-height: 1.3;
  }}
  .header-red-tag {{ color: #dc2626; font-size: 12px; letter-spacing: 1px; text-transform: uppercase; }}
  .progress-bar-wrap {{
    display: flex; align-items: center; justify-content: space-between;
    border-top: 1.5px dashed #cbd5e1; border-bottom: 1.5px dashed #cbd5e1;
    padding: 6px 4px; margin-top: 4px;
  }}
  .progress-label {{ font-size: 11px; font-weight: 800; letter-spacing: 1px; color: #64748b; text-transform: uppercase; }}
  .progress-num {{ font-size: 13px; font-weight: 900; color: #0f172a; }}

  /* Center Stage */
  .stage-center {{
    flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: center;
    position: relative; z-index: 10; margin-left: 18px;
  }}

  /* Typography Styles */
  .huge-brand-title {{
    font-size: 76px; font-weight: 900; letter-spacing: -2px; color: #0f172a; margin-bottom: 12px; text-align: center;
  }}
  .yellow-highlight-box {{
    background: #fde047; color: #0f172a; font-size: 32px; font-weight: 900;
    padding: 10px 24px; border-radius: 8px; margin-bottom: 14px; text-align: center;
    box-shadow: 0 4px 12px rgba(253, 224, 71, 0.4);
  }}
  .handwritten-sub {{
    font-size: 26px; font-style: italic; color: #64748b; font-weight: 600; text-align: center;
  }}

  /* Comparison Cards */
  .comparison-row {{
    display: flex; align-items: center; justify-content: center; gap: 24px; margin: 30px 0; width: 100%;
  }}
  .card-cross {{
    background: #fff; border: 3px solid #0f172a; border-radius: 20px;
    padding: 24px 20px; position: relative; width: 220px; text-align: center;
    box-shadow: 0 10px 20px rgba(0,0,0,0.06);
  }}
  .cross-x {{
    position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
    color: #dc2626; font-size: 120px; font-weight: 900; opacity: 0.85; pointer-events: none;
  }}
  .card-num-text {{ font-size: 24px; font-weight: 800; color: #64748b; margin-bottom: 4px; }}
  .card-sub-label {{ font-size: 16px; font-weight: 700; color: #94a3b8; }}
  .arrow-symbol {{ font-size: 36px; font-weight: 900; color: #0f172a; }}
  .card-green {{
    background: #fff; border: 3px solid #10b981; border-radius: 20px;
    padding: 24px 20px; width: 220px; text-align: center;
    box-shadow: 0 10px 25px rgba(16, 185, 129, 0.15);
  }}
  .card-user-text {{ font-size: 24px; font-weight: 900; color: #0f172a; margin-bottom: 6px; }}
  .card-priv-label {{ font-size: 16px; font-weight: 800; color: #10b981; }}

  /* Rubber Stamps */
  .stamp-box {{
    border: 3.5px solid #dc2626; color: #dc2626; font-size: 22px; font-weight: 900;
    padding: 8px 22px; border-radius: 10px; letter-spacing: 2px; text-transform: uppercase;
    transform: rotate(-8deg); display: inline-block; width: fit-content; margin-top: 16px;
    background: rgba(254, 242, 242, 0.95);
  }}
  .stamp-green {{
    border-color: #10b981; color: #10b981; transform: rotate(-5deg); background: rgba(236, 253, 245, 0.95);
  }}

  /* Phone Mockups */
  .phone-frame {{
    background: #000; border-radius: 36px; border: 4px solid #1e293b;
    overflow: hidden; position: relative; display: flex; flex-direction: column;
    box-shadow: 0 25px 50px rgba(0,0,0,0.3);
  }}
  .phone-single {{ width: 340px; height: 560px; }}
  .phone-dual {{ width: 270px; height: 460px; }}
  .phone-triple {{ width: 200px; height: 380px; }}
  .screen-img {{ width: 100%; height: 100%; object-fit: cover; background: #0f172a; }}

  /* Step Banner */
  .step-header-row {{
    display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 20px;
  }}
  .step-pill-title {{ font-size: 28px; font-weight: 900; font-style: italic; color: #0f172a; }}
  .step-fraction {{ font-size: 28px; font-weight: 900; color: #dc2626; }}

  /* CTA Card */
  .cta-card {{
    background: #fff; border: 3px solid #0f172a; border-radius: 28px;
    padding: 36px 30px; width: 100%; text-align: center;
    box-shadow: 0 20px 40px rgba(0,0,0,0.08); display: flex; flex-direction: column; gap: 16px;
  }}
  .cta-heading {{ font-size: 32px; font-weight: 900; color: #0f172a; letter-spacing: 0.5px; }}
  .cta-url-box {{
    background: #0f172a; color: #fde047; font-family: monospace; font-size: 24px; font-weight: 800;
    padding: 14px 20px; border-radius: 12px; letter-spacing: 1px;
  }}
  .cta-live-sub {{ font-size: 20px; font-weight: 800; color: #10b981; }}
  .cta-soon-sub {{ font-size: 17px; font-weight: 700; color: #64748b; }}

  .subtitles-safe-zone {{ height: 140px; }}
</style>
</head>
<body>
  <div class="notebook-margin"></div>

  <div class="header-box">
    <div class="header-row">
      <div class="day-badge">{header_day.split()[0]} <span class="day-highlight">{' '.join(header_day.split()[1:])}</span></div>
      <div class="header-meta">
        <div>{date_text}</div>
        <div class="header-red-tag">MADE IN INDIA</div>
      </div>
    </div>
    <div class="progress-bar-wrap">
      <div class="progress-label">BUILDING IN PUBLIC</div>
      <div class="progress-num">{progress_pct}</div>
    </div>
  </div>

  <div class="stage-center">
    {content_html}
  </div>

  <div class="subtitles-safe-zone"></div>
</body>
</html>"""

async def build_tab_video(
    topic: str = "VARTAA",
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
    Renders God-Level Autonomous Prompt-to-Video Reels modeled after Claude Code (anything2explainer)
    and Open-Higgsfield (wide-trace/open-higgsfield).
    Generates dynamic multi-scene layouts, Mac studio windows, waveforms, bar charts,
    and synchronized red-pill karaoke subtitles with zero rigid templates.
    """
    from playwright.async_api import async_playwright

    ffmpeg_bin = get_ffmpeg_path()
    temp_dir = Path(tempfile.mkdtemp(prefix="tab_godlevel_"))
    out_video = OUTPUT_DIR / f"godlevel_{uuid.uuid4().hex[:8]}.mp4"

    # Auto-extract URL if embedded in topic
    if not website_url:
        website_url = _extract_url_from_text(topic)
    clean_topic = topic.split("http")[0].split("(")[0].strip() or "VARTAA"

    try:
        # Step 1: Autonomous Dynamic Storyboard Synthesis (Claude Code Architecture)
        director = Prompt2VideoDirector()
        higgsfield = OpenHiggsfieldClient()

        storyboard = await director.direct(user_prompt=topic, website_url=website_url)
        scenes = storyboard.get("scenes", [])
        story_style = storyboard.get("style", "shor_explainer")
        resolved_topic = storyboard.get("topic") or clean_topic

        # If user explicitly provided script_text, inject into first scene
        if script_text and scenes:
            scenes[0]["narration_script"] = script_text

        # Step 2: Scrape URL if provided, or generate AI visual asset via Open-Higgsfield
        preview_media_path = None
        if website_url:
            if progress_cb:
                await progress_cb(f"🌐 Scraping real mobile UI from {website_url}...")
            screens = await capture_app_screens(website_url)
            preview_media_path = screens.get("welcome")
        else:
            if progress_cb:
                await progress_cb("🎨 Generating AI visual assets via Open-Higgsfield...")
            try:
                hf_asset = await higgsfield.generate_media(
                    prompt=f"{resolved_topic} user interface studio cinematography",
                    media_type="image",
                    aspect_ratio="16:9"
                )
                preview_media_path = str(hf_asset)
            except Exception as e:
                logger.warning(f"Higgsfield media generation fallback: {e}")

        # Voice selection (Hinglish/Hindi or English)
        chosen_voice = voice or ("hi-IN-MadhurNeural" if any(w in topic.lower() for w in ["vartaa", "india", "bina", "kisi", "bhai", "shor", "hai"]) else "en-US-ChristopherNeural")

        # Step 3: Synthesize Speech & ASS Karaoke per Scene
        scene_audio_files = []
        scene_snapshots = []
        scene_durations = []
        total_timeline = 0.0
        ass_dialogue_lines = []

        # Start Playwright to take high-res snapshots for each scene
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=settings.BROWSER_HEADLESS,
                args=[
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--renderer-process-limit=1",
                    "--single-process",
                    "--no-zygote",
                    "--no-first-run",
                    "--disable-extensions"
                ]
            )
            page = await browser.new_page(viewport={"width": 720, "height": 1280})

            for sc in scenes:
                sc_id = sc["id"]
                sc_script = sc.get("narration_script") or sc.get("script", "")
                sc_audio = temp_dir / f"scene_{sc_id}.mp3"
                sc_ass = temp_dir / f"scene_{sc_id}.ass"
                sc_pill = sc.get("highlight_word")
                sc_cat = sc.get("category_tag", "TECH SPOTLIGHT")
                sc_part = sc.get("part_label", f"PART 0{sc_id}")

                if progress_cb:
                    try:
                        await progress_cb(f"🎬 Composing Scene {sc_id}/{len(scenes)}: {sc_cat} ({sc_part})...")
                    except Exception:
                        pass

                # Generate speech + boundary events with red_pill theme
                k_data = await asyncio.wait_for(
                    generate_karaoke_audio_and_ass(
                        text=sc_script,
                        voice=chosen_voice,
                        audio_path=sc_audio,
                        ass_path=sc_ass,
                        font_size=46,
                        margin_v=160,
                        pill_word=sc_pill,
                        style_theme="red_pill" if story_style == "shor_explainer" else "yellow"
                    ),
                    timeout=30.0
                )
                dur = k_data["duration"]
                sc["duration"] = dur
                scene_audio_files.append(sc_audio)
                scene_durations.append(dur)

                # Render dynamic HTML Scene matching reference style
                html = render_scene_html(
                    scene=sc,
                    topic=resolved_topic,
                    preview_image_path=preview_media_path
                )
                sc_snap = temp_dir / f"snap_{sc_id}.png"
                await page.set_content(html, wait_until="domcontentloaded", timeout=10000)
                await page.screenshot(path=str(sc_snap))
                scene_snapshots.append(sc_snap)

                # Parse ASS dialogue lines and offset by total_timeline
                with open(sc_ass, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("Dialogue:"):
                            parts = line.split(",", 9)
                            if len(parts) == 10:
                                def parse_t(ts):
                                    h, m, s = ts.split(":")
                                    return int(h)*3600 + int(m)*60 + float(s)
                                s_t = parse_t(parts[1]) + total_timeline
                                e_t = parse_t(parts[2]) + total_timeline
                                parts[1] = _format_ass_time(s_t)
                                parts[2] = _format_ass_time(e_t)
                                ass_dialogue_lines.append(",".join(parts))

                total_timeline += dur

            await browser.close()

        # Step 4: Write Global Master ASS Subtitle File
        master_ass = temp_dir / "master_subtitles.ass"
        ass_header = [
            "[Script Info]",
            "ScriptType: v4.00+",
            "PlayResX: 720",
            "PlayResY: 1280",
            "ScaledBorderAndShadow: yes",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            "Style: KaraokeYellow,Arial,44,&H0015CCFA,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3.5,2,2,40,40,140,1",
            "Style: KaraokeRedPill,Arial,46,&H00481DE1,&H00000000,&H00FFFFFF,&H80000000,-1,0,0,0,100,100,0,0,1,3.5,2,2,40,40,160,1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
        ]
        with open(master_ass, "w", encoding="utf-8") as f:
            f.write("\n".join(ass_header + ass_dialogue_lines))

        # Step 5: Concat Voice Audio
        audio_concat_list = temp_dir / "audio_concat.txt"
        with open(audio_concat_list, "w", encoding="utf-8") as f:
            for af in scene_audio_files:
                f.write(f"file '{af.name}'\n")

        master_voice = temp_dir / "master_voice.mp3"
        cmd_a_merge = [
            ffmpeg_bin, "-y", "-nostdin",
            "-f", "concat", "-safe", "0",
            "-i", str(audio_concat_list),
            "-c", "copy",
            str(master_voice)
        ]
        await asyncio.to_thread(subprocess.run, cmd_a_merge, capture_output=True, timeout=20, check=True)

        # Step 6: Create Concat Demuxer for Scene Images with exact durations
        concat_scenes_txt = temp_dir / "concat_scenes.txt"
        with open(concat_scenes_txt, "w", encoding="utf-8") as f:
            for snap, d in zip(scene_snapshots, scene_durations):
                safe_snap = str(snap).replace("\\", "/")
                f.write(f"file '{safe_snap}'\n")
                f.write(f"duration {d:.2f}\n")
            if scene_snapshots:
                f.write(f"file '{str(scene_snapshots[-1]).replace(chr(92), '/')}'\n")

        # Step 7: Synthesize Lo-Fi Background Beat
        bg_music = temp_dir / "lofi_beat.mp3"
        await asyncio.to_thread(generate_ambient_soundtrack, duration=total_timeline + 2.0, genre="lofi", save_path=bg_music)

        # Step 8: Single-Pass Master Timeline Compositor with ASS Karaoke and Audio Ducking
        if progress_cb:
            try:
                await progress_cb("✨ Encoding master 9:16 viral reel with active red-pill subtitles...")
            except Exception:
                pass

        safe_ass = str(master_ass).replace("\\", "/").replace(":", r"\:")
        cmd_final = [
            ffmpeg_bin, "-y", "-nostdin",
            "-f", "concat", "-safe", "0", "-i", str(concat_scenes_txt),
            "-i", str(master_voice),
            "-i", str(bg_music),
            "-filter_complex",
            f"[0:v]ass='{safe_ass}'[v];[2:a]volume=0.15[bg];[1:a][bg]amix=inputs=2:duration=first[a]",
            "-map", "[v]",
            "-map", "[a]",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(total_timeline),
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(out_video)
        ]
        res = await asyncio.to_thread(subprocess.run, cmd_final, capture_output=True, timeout=60)
        if res.returncode != 0:
            logger.error(f"FFmpeg single-pass master encoding failed: {res.stderr}")
            # Fallback without ass filter if libass is unavailable
            cmd_fallback = [
                ffmpeg_bin, "-y", "-nostdin",
                "-f", "concat", "-safe", "0", "-i", str(concat_scenes_txt),
                "-i", str(master_voice),
                "-i", str(bg_music),
                "-filter_complex",
                "[2:a]volume=0.15[bg];[1:a][bg]amix=inputs=2:duration=first[a]",
                "-map", "0:v",
                "-map", "[a]",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
                "-c:a", "aac", "-b:a", "192k",
                "-t", str(total_timeline),
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                str(out_video)
            ]
            await asyncio.to_thread(subprocess.run, cmd_fallback, capture_output=True, timeout=60, check=True)

        logger.info(f"OpenTab Reel rendered successfully ({total_timeline:.1f}s) -> {out_video}")
        return {
            "status": "success",
            "video_path": str(out_video),
            "duration": total_timeline,
            "pipeline": story_style,
            "topic": resolved_topic,
            "scenes": len(scenes)
        }

    except Exception as e:
        logger.error(f"Error building Tab video: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
