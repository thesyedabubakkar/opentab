import pytest
from pathlib import Path
import subprocess
from tools.omniedit_engine import OmniEditEngine
from tools.ffmpeg_utils import get_ffmpeg_path

@pytest.mark.asyncio
async def test_omniedit_engine(tmp_path):
    ffmpeg_bin = get_ffmpeg_path()
    sample_video = tmp_path / "raw.mp4"

    cmd = [
        ffmpeg_bin, "-y", "-nostdin",
        "-f", "lavfi", "-i", "color=c=black:s=320x240:d=1.0:r=25",
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        str(sample_video)
    ]
    subprocess.run(cmd, capture_output=True, check=True)

    engine = OmniEditEngine()
    edited = await engine.edit_video(
        input_video=sample_video,
        edit_instruction="apply cyberpunk neon grading"
    )

    assert edited.exists()
    assert edited.stat().st_size > 0
