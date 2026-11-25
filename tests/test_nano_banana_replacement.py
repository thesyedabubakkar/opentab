import pytest
from pathlib import Path
from PIL import Image
from tools.media_gen_tool import replace_character_in_photo
from core.agent_loop import AgentEngine

@pytest.mark.asyncio
async def test_replace_character_in_photo_preserves_scene(tmp_path):
    # Create fake target image (320x480) representing desert car photo
    target_img = tmp_path / "desert_car.jpg"
    base = Image.new("RGB", (320, 480), color=(180, 140, 80)) # Desert tone
    base.save(target_img, "JPEG")

    # Run replace_character_in_photo
    res = await replace_character_in_photo(
        target_image=str(target_img),
        user_id="test_nano_user",
        prompt="Add my character in this by replacing it without effecting anything other"
    )

    assert res.get("status") == "success"
    out_p = Path(res.get("image_path"))
    assert out_p.exists()
    
    # Assert dimensions match source photo
    with Image.open(out_p) as out_im:
        assert out_im.size == (320, 480)

@pytest.mark.asyncio
async def test_agent_loop_with_target_image_replaces_photo(tmp_path):
    target_img = tmp_path / "car_target.jpg"
    base = Image.new("RGB", (400, 600), color=(40, 40, 40))
    base.save(target_img, "JPEG")

    engine = AgentEngine()
    res = await engine.handle_message(
        session_id="tg_998877",
        user_text="Add my character in this by replacing it without effecting anything other please",
        image_path=str(target_img)
    )

    assert res.get("status") == "complete"
    images = res.get("images", [])
    assert len(images) > 0
    assert Path(images[0]).exists()
