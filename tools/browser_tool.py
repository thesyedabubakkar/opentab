import asyncio
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, Optional
from bs4 import BeautifulSoup
import markdownify
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from core.config import settings, DATA_DIR

logger = logging.getLogger(__name__)

SCREENSHOTS_DIR = DATA_DIR / "screenshots"
VIDEOS_DIR = DATA_DIR / "browser_videos"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

class PlaywrightBrowser:
    _instance: Optional["PlaywrightBrowser"] = None

    def __init__(self):
        self._pw = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._lock = asyncio.Lock()
        self._last_video_path: Optional[str] = None

    @classmethod
    def get_instance(cls) -> "PlaywrightBrowser":
        if cls._instance is None:
            cls._instance = PlaywrightBrowser()
        return cls._instance

    async def _ensure_page(self) -> Page:
        async with self._lock:
            if self._page is None or self._page.is_closed():
                if self._pw is None:
                    self._pw = await async_playwright().start()
                if self._browser is None:
                    self._browser = await self._pw.chromium.launch(
                        headless=settings.BROWSER_HEADLESS,
                        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
                    )
                if self._context is None:
                    self._context = await self._browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                        viewport={"width": 1280, "height": 800},
                        record_video_dir=str(VIDEOS_DIR),
                        record_video_size={"width": 1280, "height": 800}
                    )
                self._page = await self._context.new_page()
                self._page.set_default_timeout(settings.BROWSER_TIMEOUT_MS)
            return self._page

    async def get_recorded_video(self) -> Optional[str]:
        """Flushes and retrieves the recorded video of browser actions."""
        async with self._lock:
            if self._page and not self._page.is_closed():
                try:
                    video = self._page.video
                    if video:
                        await self._page.close()
                        self._page = None
                        video_path = await video.path()
                        if video_path and Path(video_path).exists() and Path(video_path).stat().st_size > 0:
                            self._last_video_path = str(video_path)
                            return self._last_video_path
                except Exception as e:
                    logger.warning(f"Could not retrieve recorded video: {e}")
            return self._last_video_path

    async def browse_url(self, url: str) -> Dict[str, Any]:
        """Loads a URL and converts its content to clean, token-efficient Markdown."""
        page = await self._ensure_page()
        try:
            if not url.startswith("http://") and not url.startswith("https://"):
                url = f"https://{url}"

            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_timeout(1000)

            title = await page.title()
            html_content = await page.content()

            # Clean HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")
            for tag in soup(["script", "style", "svg", "noscript", "iframe", "nav", "footer"]):
                tag.decompose()

            body = soup.find("body")
            raw_text = str(body) if body else html_content
            md_text = markdownify.markdownify(raw_text, heading_style="ATX").strip()

            # Trim to prevent overwhelming LLM context window (~4000 characters)
            if len(md_text) > 4000:
                md_text = md_text[:4000] + "\n\n...[Page content truncated for brevity]..."

            return {
                "title": title,
                "url": page.url,
                "content": md_text
            }
        except Exception as e:
            logger.error(f"Failed to browse {url}: {e}")
            return {"error": str(e), "url": url}

    async def click_element(self, selector: str) -> Dict[str, Any]:
        """Clicks an element matching the given CSS selector or text."""
        page = await self._ensure_page()
        try:
            await page.click(selector, timeout=8000)
            await page.wait_for_timeout(1000)
            return {"status": "success", "message": f"Clicked element '{selector}'", "current_url": page.url}
        except Exception as e:
            return {"status": "error", "error": f"Failed to click '{selector}': {str(e)}"}

    async def fill_form(self, selector: str, text: str) -> Dict[str, Any]:
        """Fills an input field or textarea."""
        page = await self._ensure_page()
        try:
            await page.fill(selector, text, timeout=8000)
            return {"status": "success", "message": f"Filled field '{selector}' with text"}
        except Exception as e:
            return {"status": "error", "error": f"Failed to fill '{selector}': {str(e)}"}

    async def take_screenshot(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Captures a screenshot of the current page."""
        page = await self._ensure_page()
        try:
            fn = f"{name or 'screenshot'}_{uuid.uuid4().hex[:6]}.png"
            path = SCREENSHOTS_DIR / fn
            await page.screenshot(path=str(path), full_page=False)
            return {
                "status": "success",
                "screenshot_path": str(path),
                "url": page.url
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def close(self):
        """Closes browser instances."""
        async with self._lock:
            if self._page and not self._page.is_closed():
                await self._page.close()
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._pw:
                await self._pw.stop()
            self._page = None
            self._context = None
            self._browser = None
            self._pw = None

BROWSER_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "browse_url",
            "description": "Opens a website URL in the browser, loads page, and returns its readable content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Website URL to navigate to (e.g. 'https://en.wikipedia.org')"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "click_element",
            "description": "Clicks on an interactive button, link, or tab on the currently open web page.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector or text content of the element to click"}
                },
                "required": ["selector"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fill_form",
            "description": "Fills an input box or form field on the currently open web page.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector or input field name"},
                    "text": {"type": "string", "description": "The text to type into the field"}
                },
                "required": ["selector", "text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Captures a full screenshot of the currently open webpage to verify visually or send to the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Short label for the screenshot"}
                }
            }
        }
    }
]
