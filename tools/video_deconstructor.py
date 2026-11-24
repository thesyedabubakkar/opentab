import asyncio
import json
import logging
from pathlib import Path
import re
import subprocess
from typing import Any, Dict, List, Optional
from tools.ffmpeg_utils import get_ffmpeg_path, get_video_duration

logger = logging.getLogger(__name__)

class VideoDeconstructor:
    """
    Deconstructs reference videos into structured blueprints:
    - Shot cut detection (FFmpeg scene detection)
    - Pacing & duration map per scene
    - Keyframe snapshot extraction
    - Template blueprint synthesis for recreating any new topic with identical rhythm
    """
    def __init__(self):
        self.ffmpeg_bin = get_ffmpeg_path()

    async def analyze_reference_video(self, video_path: Path) -> Dict[str, Any]:
        """Runs scene cut analysis and pacing extraction on an input MP4."""
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        total_duration = get_video_duration(video_path)
        shots = await asyncio.to_thread(self._detect_scene_cuts_sync, video_path, total_duration)

        return {
            "source_video": str(video_path),
            "total_duration": total_duration,
            "scene_count": len(shots),
            "scenes": shots,
            "average_scene_duration": round(total_duration / max(1, len(shots)), 2)
        }

    def _detect_scene_cuts_sync(self, video_path: Path, total_duration: float) -> List[Dict[str, Any]]:
        """Uses FFmpeg select filter with scene score threshold to locate shot cuts."""
        # ffprobe / ffmpeg scene score
        cmd = [
            self.ffmpeg_bin, "-nostdin",
            "-i", str(video_path),
            "-filter_complex", "select='gt(scene,0.28)',metadata=print:file=-",
            "-f", "null", "-"
        ]

        res = subprocess.run(cmd, capture_output=True, text=True)
        pts_times = []
        for line in res.stdout.splitlines() + res.stderr.splitlines():
            if "pts_time:" in line:
                m = re.search(r"pts_time:([0-9\.]+)", line)
                if m:
                    t = float(m.group(1))
                    if not pts_times or (t - pts_times[-1]) >= 1.5: # min 1.5s per scene
                        pts_times.append(t)

        # Build scene intervals
        cut_points = [0.0] + [t for t in pts_times if t < total_duration]
        if not pts_times or len(cut_points) < 3:
            # Fallback heuristic pacing: split into 6 natural narrative scenes (Hook, Problem, Solution, Demo, Pricing, CTA)
            step = total_duration / 6.0
            cut_points = [round(i * step, 2) for i in range(6)]

        scenes = []
        for i in range(len(cut_points)):
            start_t = cut_points[i]
            end_t = cut_points[i+1] if i + 1 < len(cut_points) else total_duration
            dur = max(1.5, round(end_t - start_t, 2))
            scenes.append({
                "scene_id": i + 1,
                "start_time": start_t,
                "end_time": end_t,
                "duration": dur,
                "role": self._infer_scene_role(i, len(cut_points))
            })

        return scenes

    def _infer_scene_role(self, index: int, total_scenes: int) -> str:
        """Infers the viral narrative role from scene position."""
        if index == 0:
            return "viral_hook"
        elif index == 1:
            return "pain_or_comparison"
        elif index == total_scenes - 1:
            return "call_to_action"
        elif index == total_scenes - 2:
            return "pricing_or_bottomline"
        elif index == 2:
            return "feature_showcase"
        else:
            return "step_guide"

    async def map_topic_to_blueprint(
        self,
        blueprint: Dict[str, Any],
        new_topic: str,
        user_instructions: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Maps a new topic (e.g. Open Higgsfield AI) onto the exact pacing of the reference video.
        Ensures the new scenes preserve the reference video's rhythm.
        """
        ref_scenes = blueprint.get("scenes", [])
        mapped_scenes = []

        category_labels = [
            "FREE AI FILM STUDIO",
            "MEET THE TOOL",
            "MULTI-MODEL ENGINE",
            "CINEMA CONTROLS",
            "3 EASY STEPS",
            "PRICING BREAKDOWN",
            "BOTTOM LINE"
        ]

        card_types = [
            "window_preview",
            "comparison_matrix",
            "window_preview",
            "window_preview",
            "step_guide",
            "pricing_breakdown",
            "cta_card"
        ]

        for i, sc in enumerate(ref_scenes):
            sc_id = i + 1
            cat = category_labels[i % len(category_labels)]
            card_t = card_types[i % len(card_types)]
            mapped_scenes.append({
                "id": sc_id,
                "target_duration": sc.get("duration", 4.0),
                "role": sc.get("role", "feature_showcase"),
                "category_tag": cat,
                "part_label": f"PART {sc_id:02d}",
                "watermark_number": f"{sc_id:02d}",
                "card_type": card_t,
                "progress_percent": int(round((sc_id / max(1, len(ref_scenes))) * 100))
            })

        return mapped_scenes
