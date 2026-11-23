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

OUTPUT_DIR = DATA_DIR / "generated_videos"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DOC_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@700;800;900&family=Inter:wght@400;600;700&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 1280px;
    height: 720px;
    background: #090d16;
    color: #ffffff;
    font-family: 'Plus Jakarta Sans', sans-serif;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 60px 80px;
    position: relative;
    overflow: hidden;
  }
  .bg-glow {
    position: absolute;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
    top: -100px;
    right: -100px;
    pointer-events: none;
  }
  .doc-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 24px;
  }
  .series-tag {
    font-size: 14px;
    font-weight: 800;
    color: #818cf8;
    letter-spacing: 2px;
    text-transform: uppercase;
  }
  .chapter-pill {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.15);
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 14px;
    font-weight: 700;
    color: #e2e8f0;
  }
  .doc-main {
    margin: auto 0;
  }
  .chapter-title {
    font-size: 48px;
    font-weight: 900;
    letter-spacing: -1px;
    line-height: 1.15;
    margin-bottom: 16px;
    background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .chapter-desc {
    font-family: 'Inter', sans-serif;
    font-size: 22px;
    color: #94a3b8;
    line-height: 1.5;
    max-width: 900px;
  }
  .cards-grid {
    display: flex;
    gap: 20px;
    margin-top: 32px;
  }
  .info-card {
    background: rgba(30, 41, 59, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 20px 24px;
    border-radius: 16px;
    flex: 1;
  }
  .card-label {
    font-size: 13px;
    color: #818cf8;
    font-weight: 800;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 6px;
  }
  .card-val {
    font-size: 18px;
    font-weight: 800;
    color: #ffffff;
  }
  .doc-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    padding-top: 20px;
    font-size: 14px;
    color: #64748b;
    font-family: 'Inter', sans-serif;
  }
</style>
</head>
<body>
  <div class="bg-glow"></div>
  <div class="doc-header">
    <div class="series-tag">{{SERIES_TITLE}}</div>
    <div class="chapter-pill">CHAPTER {{CHAPTER_NUM}}: {{CHAPTER_NAME}}</div>
  </div>
  <div class="doc-main">
    <h1 class="chapter-title">{{HEADLINE}}</h1>
    <p class="chapter-desc">{{SUMMARY}}</p>
    <div class="cards-grid">
      {{CARDS_HTML}}
    </div>
  </div>
  <div class="doc-footer">
    <div>OPENTAB DOCUMENTARY STUDIO</div>
    <div>{{DATE}}</div>
  </div>
</body>
</html>
"""

async def build_documentary_video(
    title: str,
    chapters: List[Dict[str, Any]],
    voice: str = "en-US-ChristopherNeural"
) -> Dict[str, Any]:
    """Renders a multi-chapter documentary / explainer video."""
    from playwright.async_api import async_playwright

    ffmpeg_bin = get_ffmpeg_path()
    temp_dir = Path(tempfile.mkdtemp(prefix="doc_build_"))
    out_video = OUTPUT_DIR / f"doc_{uuid.uuid4().hex[:8]}.mp4"
    chapter_video_files = []

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=settings.BROWSER_HEADLESS,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )

            for idx, ch in enumerate(chapters, 1):
                ch_name = ch.get("chapter_name", f"Part {idx}")
                headline = ch.get("headline", title)
                summary = ch.get("summary", "")
                script = ch.get("narration", summary)

                # 1. Synthesize audio
                audio_file = temp_dir / f"audio_{idx}.mp3"
                comm = edge_tts.Communicate(script, voice)
                await comm.save(str(audio_file))

                # Measure audio duration
                duration = get_audio_duration(audio_file)

                # 2. Render cards
                cards = ch.get("cards", [])
                cards_html = ""
                for c in cards:
                    cards_html += f"""
                    <div class="info-card">
                      <div class="card-label">{c.get('label', 'KEY POINT')}</div>
                      <div class="card-val">{c.get('value', '')}</div>
                    </div>
                    """

                html_content = DOC_HTML_TEMPLATE \
                    .replace("{{SERIES_TITLE}}", title) \
                    .replace("{{CHAPTER_NUM}}", str(idx)) \
                    .replace("{{CHAPTER_NAME}}", ch_name) \
                    .replace("{{HEADLINE}}", headline) \
                    .replace("{{SUMMARY}}", summary) \
                    .replace("{{CARDS_HTML}}", cards_html) \
                    .replace("{{DATE}}", datetime.now().strftime("%B %Y").upper())

                ch_html = temp_dir / f"scene_{idx}.html"
                with open(ch_html, "w", encoding="utf-8") as f:
                    f.write(html_content)

                # 3. Capture video
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    record_video_dir=str(temp_dir),
                    record_video_size={"width": 1280, "height": 720}
                )
                page = await context.new_page()
                await page.goto(f"file:///{ch_html.resolve()}", wait_until="networkidle")
                await page.wait_for_timeout(int(duration * 1000) + 1000)

                v_handle = page.video
                await page.close()
                await context.close()
                raw_v = await v_handle.path()

                # 4. Mux scene audio and video
                ch_out = temp_dir / f"ch_out_{idx}.mp4"
                mux_cmd = [
                    ffmpeg_bin, "-y",
                    "-i", str(raw_v),
                    "-i", str(audio_file),
                    "-c:v", "libx264", "-preset", "fast",
                    "-c:a", "aac", "-b:a", "192k",
                    "-shortest",
                    str(ch_out)
                ]
                subprocess.run(mux_cmd, capture_output=True)
                chapter_video_files.append(ch_out)

            await browser.close()

        # Step 5: Concat all chapters into final documentary
        concat_txt = temp_dir / "concat.txt"
        with open(concat_txt, "w") as f:
            for cv in chapter_video_files:
                f.write(f"file '{cv.resolve()}'\n")

        concat_cmd = [
            ffmpeg_bin, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_txt),
            "-c", "copy",
            str(out_video)
        ]
        subprocess.run(concat_cmd, check=True)

        return {
            "status": "success",
            "video_path": str(out_video),
            "title": title,
            "chapters_count": len(chapters)
        }

    except Exception as e:
        logger.error(f"Failed to generate documentary video: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

DOCUMENTARY_SCHEMA = {
    "type": "function",
    "function": {
        "name": "generate_documentary_video",
        "description": "Generates a multi-chapter documentary or long explainer video with chapters, slides, and voiceover.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Documentary title"},
                "chapters": {
                    "type": "array",
                    "description": "List of chapters, each with 'chapter_name', 'headline', 'summary', 'narration', and 'cards'",
                    "items": {
                        "type": "object",
                        "properties": {
                            "chapter_name": {"type": "string"},
                            "headline": {"type": "string"},
                            "summary": {"type": "string"},
                            "narration": {"type": "string"},
                            "cards": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "label": {"type": "string"},
                                        "value": {"type": "string"}
                                    }
                                }
                            }
                        },
                        "required": ["headline", "narration"]
                    }
                },
                "voice": {"type": "string", "description": "Voice identifier (e.g. 'en-US-ChristopherNeural', 'hi-IN-MadhurNeural')"}
            },
            "required": ["title", "chapters"]
        }
    }
}
