import pytest
from pathlib import Path
import subprocess
from tools.motion_transitions import MotionTransitionEngine
from tools.ffmpeg_utils import get_ffmpeg_path

@pytest.mark.asyncio
async def test_motion_transitions(tmp_path):
    ffmpeg_bin = get_ffmpeg_path()
    clip1 = tmp_path / "c1.mp4"
    clip2 = tmp_path / "c2.mp4"

    # Create two test color clips of 2 seconds each
    for clip, color in [(clip1, "blue"), (clip2, "red")]:
        cmd = [
            ffmpeg_bin, "-y", "-nostdin",
            "-f", "lavfi", "-i", f"color=c={color}:s=320x240:d=2.0:r=25",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            str(clip)
        ]
        subprocess.run(cmd, capture_output=True, check=True)

    engine = MotionTransitionEngine()
    out = tmp_path / "transition_test.mp4"
    res = await engine.compose_with_transitions(
        clips=[clip1, clip2],
        durations=[2.0, 2.0],
        transitions=["zoomin"],
        transition_duration=0.5,
        output_path=out
    )

    assert res.exists()
    assert res.stat().st_size > 1000
