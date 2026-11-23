import os
import pytest
from tools.browser_tool import PlaywrightBrowser

@pytest.mark.asyncio
async def test_playwright_navigation_and_screenshot():
    browser = PlaywrightBrowser.get_instance()
    try:
        # Navigate to example.com
        res = await browser.browse_url("https://example.com")
        assert "Example Domain" in res["title"]
        assert "example" in res["content"].lower()

        # Capture screenshot
        shot = await browser.take_screenshot("test_example")
        assert shot["status"] == "success"
        assert os.path.exists(shot["screenshot_path"])
        assert os.path.getsize(shot["screenshot_path"]) > 0
    finally:
        await browser.close()
