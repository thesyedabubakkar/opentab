import os
from pathlib import Path
import pytest
from tools.media_gen_tool import generate_image, generate_voice_note
from tools.browser_tool import PlaywrightBrowser

@pytest.mark.asyncio
async def test_generate_image():
    res = await generate_image("a cute robot assistant reading a book", width=512, height=512)
    assert res["status"] == "success"
    img_path = res["image_path"]
    assert Path(img_path).exists()
    assert Path(img_path).stat().st_size > 1000

@pytest.mark.asyncio
async def test_generate_voice_note():
    res = await generate_voice_note("Hello! I am OpenTab, your personal assistant.")
    assert res["status"] == "success"
    audio_path = res["audio_path"]
    assert Path(audio_path).exists()
    assert Path(audio_path).stat().st_size > 1000

@pytest.mark.asyncio
async def test_browser_video_recording():
    browser = PlaywrightBrowser.get_instance()
    try:
        await browser.browse_url("https://example.com")
        video_path = await browser.get_recorded_video()
        if video_path:
            assert Path(video_path).exists()
            assert Path(video_path).stat().st_size > 0
    finally:
        await browser.close()
