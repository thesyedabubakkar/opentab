import pytest
from pathlib import Path
from tools.tab_studio_engine import _classify_pipeline, _extract_url_from_text
from tools.karaoke_subtitles import _format_ass_time, generate_karaoke_audio_and_ass

def test_pipeline_classification():
    assert _classify_pipeline("Trip to Joshua Tree", None, ["clip1.mp4"]) == "footage_recap"
    assert _classify_pipeline("VARTAA", "https://vartaa.techorbitpvt.com", None) == "app_launch"
    assert _classify_pipeline("How to build an AI agent", None, None) == "animated_explainer"
    assert _classify_pipeline("Signal From Tomorrow Sci-Fi film trailer", None, None) == "cinematic_film"

def test_extract_url():
    assert _extract_url_from_text("Check vartaa.techorbitpvt.com now") == "https://vartaa.techorbitpvt.com"
    assert _extract_url_from_text("Visit https://example.com/app") == "https://example.com/app"
    assert _extract_url_from_text("No url here") is None

def test_ass_time_format():
    assert _format_ass_time(0.0) == "0:00:00.00"
    assert _format_ass_time(1.25) == "0:00:01.25"
    assert _format_ass_time(65.5) == "0:01:05.50"

@pytest.mark.asyncio
async def test_karaoke_ass_generation(tmp_path):
    audio_path = tmp_path / "test.mp3"
    ass_path = tmp_path / "test.ass"
    res = await generate_karaoke_audio_and_ass(
        text="Bina phone number chat? Sovereign privacy.",
        voice="hi-IN-MadhurNeural",
        audio_path=audio_path,
        ass_path=ass_path
    )
    assert res["duration"] > 0
    assert audio_path.exists()
    assert ass_path.exists()
    content = ass_path.read_text(encoding="utf-8")
    assert "[V4+ Styles]" in content
    assert "KaraokeYellow" in content
    assert r"{\k" in content
