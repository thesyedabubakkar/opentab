import asyncio
from pathlib import Path
import pytest
from core.storyboard import generate_default_storyboard, VideoProductionPlan, Scene
from tools.openmontage_assets import synthesize_scene_voice, generate_ambient_soundtrack
from tools.montage_compositor import build_openmontage_video

def test_storyboard_generation():
    plan = generate_default_storyboard(topic="VARTAA Communication", aspect_ratio="9:16")
    assert len(plan.scenes) == 3
    assert plan.aspect_ratio == "9:16"
    assert "VARTAA" in plan.title

@pytest.mark.asyncio
async def test_ambient_soundtrack_generation(tmp_path):
    music_file = tmp_path / "ambient_test.mp3"
    res_path = generate_ambient_soundtrack(duration=3.0, genre="tech_ambient", save_path=music_file)
    assert res_path.exists()
    assert res_path.stat().st_size > 1000

@pytest.mark.asyncio
async def test_scene_voice_synthesis(tmp_path):
    voice_file = tmp_path / "voice_test.mp3"
    res_path, dur = await synthesize_scene_voice("This is a test of OpenMontage audio.", save_path=voice_file)
    assert res_path.exists()
    assert dur > 1.0
