import asyncio
import pytest
from pathlib import Path
from tools.tab_studio_engine import build_tab_video

@pytest.mark.asyncio
async def test_e2e_godlevel_video_generation():
    progress_updates = []
    async def _progress(text: str):
        progress_updates.append(text)

    res = await build_tab_video(
        topic="Open Higgsfield AI filmmaking studio",
        progress_cb=_progress
    )

    assert res["status"] == "success"
    video_path = Path(res["video_path"])
    assert video_path.exists()
    assert video_path.stat().st_size > 100_000
    assert res["scenes"] >= 4
    assert len(progress_updates) > 0
    print(f"\n[+] Generated God-Level Reel: {video_path} ({res['duration']:.1f}s, {video_path.stat().st_size / 1024 / 1024:.2f} MB)")
