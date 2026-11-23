import pytest
from pathlib import Path
from tools.registry import ToolRegistry
from tools.reel_builder import build_viral_reel
from tools.ffmpeg_utils import get_ffmpeg_path

@pytest.mark.asyncio
async def test_tool_registry_schemas():
    registry = ToolRegistry()
    schemas = registry.get_all_schemas()
    schema_names = [s["function"]["name"] for s in schemas if "function" in s]

    assert "generate_viral_reel" in schema_names
    assert "generate_documentary_video" in schema_names
    assert "search_web" in schema_names
    assert "browse_url" in schema_names
    assert "generate_image" in schema_names

def test_ffmpeg_available():
    bin_path = get_ffmpeg_path()
    assert bin_path is not None
    assert len(bin_path) > 0

@pytest.mark.asyncio
async def test_build_viral_reel_mock():
    # Test short reel generation
    res = await build_viral_reel(
        product_name="TEST_APP",
        hook_title="POV: No OTP needed",
        tagline="Next gen messaging",
        old_label="Phone SMS",
        new_label="@testuser",
        stamp_text="100% PRIVATE",
        script_text="Test reel short script."
    )
    assert res["status"] == "success"
    assert "video_path" in res
    assert Path(res["video_path"]).exists()
    assert Path(res["video_path"]).stat().st_size > 10000
