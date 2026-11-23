import json
import logging
from typing import Any, Dict, List, Optional
from tools.search_tool import search_web, SEARCH_SCHEMA
from tools.browser_tool import PlaywrightBrowser, BROWSER_SCHEMAS
from tools.code_runner import run_python_code, CODE_RUNNER_SCHEMA
from tools.reminders import set_user_preference, PREFERENCE_SCHEMA
from tools.media_gen_tool import (
    generate_image,
    generate_video,
    generate_voice_note,
    MEDIA_SCHEMAS
)
from tools.reel_builder import build_viral_reel, VIRAL_REEL_SCHEMA
from tools.documentary_builder import build_documentary_video, DOCUMENTARY_SCHEMA
from tools.composio_tool import ComposioToolHub

logger = logging.getLogger(__name__)

class ToolRegistry:
    def __init__(self):
        self.browser = PlaywrightBrowser.get_instance()
        self.composio = ComposioToolHub()
        self.latest_screenshot: Optional[str] = None

    def set_latest_screenshot(self, path: str):
        self.latest_screenshot = path

    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """Collects all tool definition schemas for LLM function calling."""
        schemas = [
            SEARCH_SCHEMA,
            *BROWSER_SCHEMAS,
            CODE_RUNNER_SCHEMA,
            PREFERENCE_SCHEMA,
            *MEDIA_SCHEMAS,
            VIRAL_REEL_SCHEMA,
            DOCUMENTARY_SCHEMA
        ]
        schemas.extend(self.composio.get_schemas())
        return schemas

    async def dispatch(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Dispatches tool execution by name with parsed arguments."""
        logger.info(f"Dispatching tool '{tool_name}' with arguments: {arguments}")

        # Search
        if tool_name == "search_web":
            return await search_web(
                query=arguments.get("query", ""),
                max_results=int(arguments.get("max_results", 5))
            )

        # Video Generation - 9:16 Viral Reel
        elif tool_name == "generate_viral_reel":
            shot = arguments.get("screenshot_path") or self.latest_screenshot
            return await build_viral_reel(
                product_name=arguments.get("product_name", "VARTAA"),
                hook_title=arguments.get("hook_title", "Bina phone number chat?"),
                tagline=arguments.get("tagline", "Privacy ab wapas aayegi."),
                old_label=arguments.get("old_label", "+91 98XXX Phone OTP"),
                old_sub=arguments.get("old_sub", "Data leak risk"),
                new_label=arguments.get("new_label", "@username"),
                new_sub=arguments.get("new_sub", "100% Private"),
                stamp_text=arguments.get("stamp_text", "NO PHONE · NO OTP"),
                script_text=arguments.get("script_text", "Phone number se sign up karke privacy ka tamasha khatam."),
                screenshot_path=shot,
                day_number=int(arguments.get("day_number", 1)),
                progress_pct=int(arguments.get("progress_pct", 29)),
                voice=arguments.get("voice", "hi-IN-MadhurNeural")
            )

        # Video Generation - Multi-Chapter Documentary
        elif tool_name == "generate_documentary_video":
            return await build_documentary_video(
                title=arguments.get("title", "OpenTab Documentary"),
                chapters=arguments.get("chapters", []),
                voice=arguments.get("voice", "en-US-ChristopherNeural")
            )

        # Media Generation
        elif tool_name == "generate_image":
            return await generate_image(
                prompt=arguments.get("prompt", ""),
                width=int(arguments.get("width", 1024)),
                height=int(arguments.get("height", 1024))
            )
        elif tool_name == "generate_video":
            return await generate_video(prompt=arguments.get("prompt", ""))
        elif tool_name == "generate_voice_note":
            return await generate_voice_note(
                text=arguments.get("text", ""),
                voice=arguments.get("voice", "en-US-ChristopherNeural")
            )

        # Browser
        elif tool_name == "browse_url":
            return await self.browser.browse_url(url=arguments.get("url", ""))
        elif tool_name == "click_element":
            return await self.browser.click_element(selector=arguments.get("selector", ""))
        elif tool_name == "fill_form":
            return await self.browser.fill_form(
                selector=arguments.get("selector", ""),
                text=arguments.get("text", "")
            )
        elif tool_name == "take_screenshot":
            res = await self.browser.take_screenshot(name=arguments.get("name", "screenshot"))
            if isinstance(res, dict) and "screenshot_path" in res:
                self.latest_screenshot = res["screenshot_path"]
            return res

        # Code Runner
        elif tool_name == "run_python_code":
            return await run_python_code(code=arguments.get("code", ""))

        # User Preferences
        elif tool_name == "set_user_preference":
            return await set_user_preference(
                key=arguments.get("key", ""),
                value=arguments.get("value", "")
            )

        # Fallback to Composio
        else:
            return await self.composio.execute_action(tool_name, arguments)
