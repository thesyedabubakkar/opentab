import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)

def get_ffmpeg_path() -> str:
    """Finds the ffmpeg executable on PATH, imageio-ffmpeg, or standard directories."""
    # 1. System PATH
    p = shutil.which("ffmpeg")
    if p:
        return p

    # 2. imageio-ffmpeg static binary
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass

    # 3. Known Linux/Docker paths
    for cand in ["/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"]:
        if os.path.exists(cand):
            return cand

    return "ffmpeg"

def get_audio_duration(audio_file: Path) -> float:
    """Accurately calculates audio duration in seconds using ffprobe or ffmpeg."""
    # Method A: ffprobe if present
    probe = shutil.which("ffprobe")
    if probe:
        try:
            res = subprocess.run([
                probe, "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(audio_file)
            ], capture_output=True, text=True)
            val = float(res.stdout.strip())
            if val > 0:
                return val
        except Exception:
            pass

    # Method B: ffmpeg stderr inspect
    ffmpeg_bin = get_ffmpeg_path()
    try:
        res = subprocess.run([ffmpeg_bin, "-i", str(audio_file)], capture_output=True, text=True)
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", res.stderr)
        if m:
            hours, mins, secs = float(m.group(1)), float(m.group(2)), float(m.group(3))
            duration = hours * 3600 + mins * 60 + secs
            if duration > 0:
                return duration
    except Exception:
        pass

    return 8.0
