import json
import logging
from typing import Any, Dict, List
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
from tools.composio_tool import ComposioToolHub

logger = logging.getLogger(__name__)

class ToolRegistry:
    def __init__(self):
        self.browser = PlaywrightBrowser.get_instance()
        self.composio = ComposioToolHub()

    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """Collects all tool definition schemas for LLM function calling."""
        schemas = [
            SEARCH_SCHEMA,
            *BROWSER_SCHEMAS,
            CODE_RUNNER_SCHEMA,
            PREFERENCE_SCHEMA,
            *MEDIA_SCHEMAS
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
            return await generate_voice_note(text=arguments.get("text", ""))

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
            return await self.browser.take_screenshot(name=arguments.get("name", "screenshot"))

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
