import pytest
from pathlib import Path
from tools.character_consistency_engine import CharacterProfileManager

@pytest.mark.asyncio
async def test_character_profile_registration(tmp_path):
    mgr = CharacterProfileManager()
    mgr.base_dir = tmp_path

    # Fake face image
    face_img = tmp_path / "test_selfie.jpg"
    face_img.write_bytes(b"\xFF\xD8\xFF\xE0fakejpeg")

    profile = await mgr.register_user_face("user_999", face_img, character_name="Abubakkar")
    assert profile["user_id"] == "user_999"
    assert mgr.has_registered_character("user_999")
    
    master_face = mgr.get_master_face("user_999")
    assert master_face is not None
    assert master_face.exists()
