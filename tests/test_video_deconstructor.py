import pytest
from pathlib import Path
import subprocess
from tools.video_deconstructor import VideoDeconstructor
from tools.ffmpeg_utils import get_ffmpeg_path

@pytest.mark.asyncio
async def test_video_deconstructor(tmp_path):
    ffmpeg_bin = get_ffmpeg_path()
    sample_video = tmp_path / "sample_ref.mp4"

    # Create a 4-second video
    cmd = [
        ffmpeg_bin, "-y", "-nostdin",
        "-f", "lavfi", "-i", "testsrc=size=320x240:rate=25",
        "-t", "4.0",
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        str(sample_video)
    ]
    subprocess.run(cmd, capture_output=True, check=True)

    deconstructor = VideoDeconstructor()
    blueprint = await deconstructor.analyze_reference_video(sample_video)

    assert blueprint["scene_count"] >= 1
    assert blueprint["total_duration"] >= 3.9

    mapped = await deconstructor.map_topic_to_blueprint(blueprint, new_topic="Open Higgsfield AI")
    assert len(mapped) == blueprint["scene_count"]
    assert mapped[0]["part_label"] == "PART 01"
