import asyncio
import logging
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any, Callable, Dict, List, Optional
import uuid

from core.config import DATA_DIR
from core.storyboard import VideoProductionPlan, Scene, generate_default_storyboard
from tools.ffmpeg_utils import get_ffmpeg_path, get_audio_duration
from tools.openmontage_assets import (
    fetch_scene_visual,
    synthesize_scene_voice,
    generate_ambient_soundtrack
)

logger = logging.getLogger(__name__)

OUTPUT_DIR = DATA_DIR / "generated_videos"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

async def build_openmontage_video(
    plan: Optional[VideoProductionPlan] = None,
    topic: str = "The Future of AI",
    aspect_ratio: str = "9:16",
    voice: str = "en-US-ChristopherNeural",
    music_genre: str = "tech_ambient",
    progress_cb: Optional[Callable[[str], Any]] = None
) -> Dict[str, Any]:
    """
    Renders an agentic multi-scene video montage inspired by OpenMontage.
    Coordinates multi-asset visual generation, per-scene neural voice,
    ambient music mixing with ducking, and seamless transitions.
    """
    ffmpeg_bin = get_ffmpeg_path()
    temp_dir = Path(tempfile.mkdtemp(prefix="montage_build_"))
    out_video = OUTPUT_DIR / f"montage_{uuid.uuid4().hex[:8]}.mp4"

    if plan is None or not plan.scenes:
        plan = generate_default_storyboard(
            topic=topic,
            aspect_ratio=aspect_ratio,
            voice=voice,
            music_genre=music_genre
        )

    w, h = (720, 1280) if plan.aspect_ratio == "9:16" else (1280, 720)

    try:
        scene_video_clips = []
        total_duration = 0.0

        # Phase 1: Generate assets and render each scene
        for idx, sc in enumerate(plan.scenes, start=1):
            if progress_cb:
                await progress_cb(f"🎬 Scene {idx}/{len(plan.scenes)}: Generating visuals & voice for '{sc.title}'...")

            # 1. Voiceover
            voice_path = temp_dir / f"scene_{idx}_audio.mp3"
            _, scene_dur = await synthesize_scene_voice(
                text=sc.voice_script,
                voice=plan.voice_name,
                save_path=voice_path
            )
            sc.duration = scene_dur
            total_duration += scene_dur

            # 2. Visual asset
            vis_path = temp_dir / f"scene_{idx}_visual.jpg"
            await fetch_scene_visual(
                visual_prompt=sc.visual_prompt,
                aspect_ratio=plan.aspect_ratio,
                save_path=vis_path
            )

            # 3. Render individual scene clip with motion
            scene_clip = temp_dir / f"scene_{idx}_clip.mp4"
            # Motion zoom formula based on duration
            frames = int(scene_dur * 24)
            if sc.motion_type == "zoom_in":
                vf_motion = f"zoompan=z='min(zoom+0.0015,1.15)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps=24"
            elif sc.motion_type == "pan_right":
                vf_motion = f"zoompan=z=1.08:d={frames}:x='(iw-iw/zoom)*(on/{frames})':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps=24"
            else:
                vf_motion = f"zoompan=z='if(lte(zoom,1.0),1.15,max(1.0,zoom-0.0015))':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps=24"

            # Draw clean subtitle bar on scene
            safe_script = sc.voice_script.replace("'", "").replace(":", "")[:80]
            vf_filter = f"{vf_motion},drawbox=y=ih-140:color=black@0.65:width=iw:height=100:t=fill"

            scene_cmd = [
                ffmpeg_bin, "-y",
                "-loop", "1", "-i", str(vis_path),
                "-i", str(voice_path),
                "-t", str(scene_dur),
                "-vf", vf_filter,
                "-c:v", "libx264", "-preset", "ultrafast",
                "-c:a", "aac", "-b:a", "128k",
                "-pix_fmt", "yuv420p",
                str(scene_clip)
            ]
            res = subprocess.run(scene_cmd, capture_output=True, text=True)
            if res.returncode == 0 and scene_clip.exists():
                scene_video_clips.append(scene_clip)
            else:
                logger.warning(f"Scene {idx} render error: {res.stderr}")

        if not scene_video_clips:
            raise RuntimeError("Failed to render any scene clips.")

        # Phase 2: Concatenate all scene clips
        if progress_cb:
            await progress_cb(f"🎞️ Splicing {len(scene_video_clips)} scenes & composing master timeline...")

        concat_list_file = temp_dir / "concat_list.txt"
        with open(concat_list_file, "w", encoding="utf-8") as f:
            for clip in scene_video_clips:
                f.write(f"file '{clip.resolve().as_posix()}'\n")

        raw_joined = temp_dir / "raw_joined.mp4"
        subprocess.run([
            ffmpeg_bin, "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_list_file),
            "-c", "copy",
            str(raw_joined)
        ], capture_output=True, check=True)

        # Phase 3: Generate Background Soundtrack and Mix with Audio Ducking
        if progress_cb:
            await progress_cb(f"🎵 Mixing {plan.music_genre} soundtrack with voice ducking...")

        music_path = temp_dir / "ambient_music.mp3"
        generate_ambient_soundtrack(
            duration=total_duration,
            genre=plan.music_genre,
            save_path=music_path
        )

        # Mix voice and music: Music at volume 0.16 (subtle bed), voice at 1.0
        final_cmd = [
            ffmpeg_bin, "-y",
            "-i", str(raw_joined),
            "-i", str(music_path),
            "-filter_complex", "[0:a]volume=1.0[a0];[1:a]volume=0.16[a1];[a0][a1]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(out_video)
        ]
        subprocess.run(final_cmd, capture_output=True, check=True)

        logger.info(f"OpenMontage production complete: {out_video} (Duration: {total_duration:.1f}s)")
        return {
            "status": "success",
            "video_path": str(out_video),
            "title": plan.title,
            "duration": total_duration,
            "scene_count": len(scene_video_clips),
            "aspect_ratio": plan.aspect_ratio
        }

    except Exception as e:
        logger.error(f"OpenMontage build failed: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
