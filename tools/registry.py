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
    swap_character_face,
    MEDIA_SCHEMAS
)
from tools.reel_builder import build_viral_reel, VIRAL_REEL_SCHEMA
from tools.montage_compositor import build_openmontage_video
from core.storyboard import VideoProductionPlan, Scene, generate_default_storyboard
from tools.documentary_builder import build_documentary_video, DOCUMENTARY_SCHEMA
from tools.composio_tool import ComposioToolHub

from tools.tab_studio_engine import build_tab_video

logger = logging.getLogger(__name__)

OPENMONTAGE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "create_openmontage_video",
        "description": "Universal 4-Pipeline Video Studio (modeled after Tab tab.bot and OpenMontage). Generates App Launch Reels with real mobile screenshots, Raw Footage Recaps, Kinetic Animated Explainers, or Cinematic Trailers with active yellow word-by-word karaoke subtitles.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Topic, brand, or product name (e.g. 'VARTAA', 'OpenTab', 'How AI Agents Work')"},
                "website_url": {"type": "string", "description": "Website or web app URL to scrape real mobile screenshots from (e.g. 'https://vartaa.techorbitpvt.com')"},
                "pipeline": {
                    "type": "string",
                    "enum": ["app_launch", "footage_recap", "animated_explainer", "cinematic_film"],
                    "description": "Production pipeline: 'app_launch' (grid notebook, 3D phone with real screenshots, stamps), 'footage_recap' (cutting clips into recap), 'animated_explainer' (cards, tutorials), 'cinematic_film' (trailer, letterbox)"
                },
                "hook_title": {"type": "string", "description": "Catchy headline or opening question (e.g. 'Bina Phone Number Chat?')"},
                "script_text": {"type": "string", "description": "Spoken voiceover script (15-35 words). Use natural Hinglish/Hindi for Indian apps, or English for international products."},
                "voice": {"type": "string", "description": "Neural voice: 'hi-IN-MadhurNeural', 'hi-IN-SwaraNeural', 'en-US-ChristopherNeural', 'en-US-JennyNeural', 'en-GB-RyanNeural'"},
                "stamp_text": {"type": "string", "description": "Angled callout stamp (e.g. 'CONSENT FIRST', 'ZERO PHONE NUMBER', '100% AUTONOMOUS')"},
                "day_number": {"type": "integer", "description": "Day number for build-in-public badge (e.g. 1)"},
                "progress_pct": {"type": "integer", "description": "Progress percentage for header strip (e.g. 91)"}
            },
            "required": ["topic"]
        }
    }
}

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
            OPENMONTAGE_SCHEMA,
            DOCUMENTARY_SCHEMA
        ]
        schemas.extend(self.composio.get_schemas())
        return schemas

    async def dispatch(self, tool_name: str, arguments: Dict[str, Any], progress_cb: Optional[Any] = None) -> Any:
        """Dispatches tool execution by name with parsed arguments."""
        logger.info(f"Dispatching tool '{tool_name}' with arguments: {arguments}")

        # Search
        if tool_name == "search_web":
            return await search_web(
                query=arguments.get("query", ""),
                max_results=int(arguments.get("max_results", 5))
            )

        # Video Generation - Universal 4-Pipeline Studio Engine (Tab.bot / OpenMontage)
        elif tool_name in ["generate_viral_reel", "create_openmontage_video"]:
            from tools.tab_studio_engine import _extract_url_from_text
            product_name = arguments.get("product_name") or arguments.get("topic") or arguments.get("prompt") or arguments.get("idea") or "OpenTab"
            website_url = arguments.get("website_url")
            if not website_url:
                combined_text = f"{product_name} {arguments.get('topic', '')} {arguments.get('script_text', '')} {arguments.get('script', '')}"
                website_url = _extract_url_from_text(combined_text)
            pipeline = arguments.get("pipeline")
            hook_title = arguments.get("hook_title")
            script_text = arguments.get("script_text") or arguments.get("script")
            voice = arguments.get("voice")
            stamp_text = arguments.get("stamp_text")
            day_number = arguments.get("day_number", 1)
            progress_pct = arguments.get("progress_pct", 91)
            aspect_ratio = arguments.get("aspect_ratio", "9:16")
            user_id = arguments.get("user_id")
            reference_video = arguments.get("reference_video")
            use_transitions = arguments.get("use_transitions", True)

            return await build_tab_video(
                topic=product_name,
                website_url=website_url,
                pipeline=pipeline,
                hook_title=hook_title,
                script_text=script_text,
                voice=voice,
                aspect_ratio=aspect_ratio,
                day_number=int(day_number) if day_number else 1,
                progress_pct=int(progress_pct) if progress_pct else 91,
                stamp_text=stamp_text,
                user_id=str(user_id) if user_id else None,
                reference_video=reference_video,
                use_transitions=use_transitions,
                progress_cb=progress_cb
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
        elif tool_name in ["swap_character_face", "replace_character_in_image"]:
            return await swap_character_face(
                prompt=arguments.get("prompt", ""),
                target_image=arguments.get("target_image"),
                user_id=arguments.get("user_id"),
                character_features=arguments.get("character_features")
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
