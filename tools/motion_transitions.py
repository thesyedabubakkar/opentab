import asyncio
import logging
from pathlib import Path
import subprocess
from typing import List, Optional
from tools.ffmpeg_utils import get_ffmpeg_path, get_audio_duration

logger = logging.getLogger(__name__)

SUPPORTED_TRANSITIONS = {
    "zoomin",
    "smoothleft",
    "smoothright",
    "slideleft",
    "slideright",
    "wipeleft",
    "wiperight",
    "dissolve",
    "fadeblack",
    "circlecrop"
}

class MotionTransitionEngine:
    """
    Constructs multi-scene video sequences linked with dynamic FFmpeg xfade transitions.
    Supported transitions: zoomin, smoothleft, smoothright, slideleft, wiperight, dissolve, fadeblack.
    """
    def __init__(self):
        self.ffmpeg_bin = get_ffmpeg_path()

    async def compose_with_transitions(
        self,
        clips: List[Path],
        durations: List[float],
        transitions: Optional[List[str]] = None,
        transition_duration: float = 0.5,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Chains clips together using FFmpeg xfade.
        If transitions is not provided or shorter than clips-1, cycles through a default dynamic palette.
        """
        if not clips:
            raise ValueError("No video clips provided for transitions.")
        if len(clips) == 1:
            return clips[0]

        if not output_path:
            output_path = clips[0].parent / "transition_master.mp4"

        # Validate transition list
        palette = ["zoomin", "smoothleft", "dissolve", "smoothright", "fadeblack", "slideright"]
        final_transitions = []
        for i in range(len(clips) - 1):
            if transitions and i < len(transitions) and transitions[i] in SUPPORTED_TRANSITIONS:
                final_transitions.append(transitions[i])
            else:
                final_transitions.append(palette[i % len(palette)])

        return await asyncio.to_thread(
            self._execute_xfade_sync,
            clips,
            durations,
            final_transitions,
            transition_duration,
            output_path
        )

    def _execute_xfade_sync(
        self,
        clips: List[Path],
        durations: List[float],
        transitions: List[str],
        t_dur: float,
        out_path: Path
    ) -> Path:
        """Constructs and executes the complex filtergraph for multi-input xfade."""
        cmd = [self.ffmpeg_bin, "-y", "-nostdin"]

        # Add all inputs
        for c in clips:
            cmd.extend(["-i", str(c)])

        # Build filter_complex string
        # [0:v][1:v]xfade=transition=zoomin:duration=0.5:offset=OFFSET[v01];
        # [v01][2:v]xfade=transition=smoothleft:duration=0.5:offset=OFFSET[v02]...
        filter_parts = []
        last_v = "[0:v]"
        current_offset = durations[0] - t_dur

        for i, trans in enumerate(transitions):
            next_input = f"[{i+1}:v]"
            out_v = f"[vx{i}]" if i < len(transitions) - 1 else "[outv]"
            # Ensure offset is positive
            safe_offset = max(0.1, current_offset)
            filter_parts.append(
                f"{last_v}{next_input}xfade=transition={trans}:duration={t_dur:.2f}:offset={safe_offset:.2f}{out_v}"
            )
            last_v = out_v
            if i + 1 < len(durations):
                current_offset = (safe_offset + durations[i+1]) - t_dur

        filter_complex_str = ";".join(filter_parts)

        cmd.extend([
            "-filter_complex", filter_complex_str,
            "-map", "[outv]",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            str(out_path)
        ])

        logger.info(f"Executing FFmpeg xfade transition chain across {len(clips)} clips...")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            logger.warning(f"FFmpeg xfade chain failed ({res.stderr}). Falling back to simple concat.")
            return self._fallback_concat(clips, out_path)

        return out_path

    def _fallback_concat(self, clips: List[Path], out_path: Path) -> Path:
        """Safe fallback to standard concat demuxer if xfade fails on mismatched resolution/framerate."""
        concat_txt = out_path.parent / "fallback_concat.txt"
        with open(concat_txt, "w", encoding="utf-8") as f:
            for c in clips:
                f.write(f"file '{c.name}'\n")

        cmd = [
            self.ffmpeg_bin, "-y", "-nostdin",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_txt),
            "-c", "copy",
            str(out_path)
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        return out_path
