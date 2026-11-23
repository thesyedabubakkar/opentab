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
from tools.montage_compositor import build_openmontage_video
from core.storyboard import VideoProductionPlan, Scene, generate_default_storyboard
from tools.documentary_builder import build_documentary_video, DOCUMENTARY_SCHEMA
from tools.composio_tool import ComposioToolHub

logger = logging.getLogger(__name__)

OPENMONTAGE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "create_openmontage_video",
        "description": "Generates a true multi-scene cinematic video montage with distinct visual cuts, neural voiceover per scene, and ambient music ducking (inspired by OpenMontage/tab.bot). Use for all video reels, shorts, stories, and marketing videos.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Topic, brand, or product name"},
                "hook_title": {"type": "string", "description": "Catchy dramatic hook question or opening headline"},
                "script_text": {"type": "string", "description": "Narrative spoken voiceover script (30-50 words)"},
                "aspect_ratio": {"type": "string", "enum": ["9:16", "16:9"], "description": "Aspect ratio: '9:16' for vertical Reels/Shorts/TikTok, or '16:9' for widescreen"},
                "music_genre": {"type": "string", "enum": ["tech_ambient", "cinematic", "lofi"], "description": "Ambient soundtrack genre"},
                "voice": {"type": "string", "description": "Neural voice name (e.g. 'en-US-ChristopherNeural', 'en-US-JennyNeural', 'hi-IN-MadhurNeural')"}
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

        # Video Generation - OpenMontage Multi-Scene Cinematic Production
        elif tool_name in ["generate_viral_reel", "create_openmontage_video"]:
            product_name = arguments.get("product_name") or arguments.get("topic") or "OpenTab"
            hook_title = arguments.get("hook_title") or f"The Future of {product_name}"
            script_text = arguments.get("script_text") or arguments.get("script") or ""
            voice = arguments.get("voice") or "en-US-ChristopherNeural"
            theme = arguments.get("theme") or "dark_glass"
            genre = arguments.get("music_genre") or ("tech_ambient" if theme == "dark_glass" else ("cinematic" if theme == "cinematic" else "lofi"))
            aspect_ratio = arguments.get("aspect_ratio", "9:16")
            shot = arguments.get("screenshot_path") or self.latest_screenshot

            # Construct high-converting 4-scene narrative storyboard
            hook_script = hook_title if len(hook_title) > 10 else f"What if everything you knew about {product_name} was about to change?"
            solution_script = script_text if script_text else f"Meet {product_name}. Built from the ground up for speed, elegance, and total autonomy."
            cta_script = f"Experience the future of {product_name} today."

            plan = VideoProductionPlan(
                title=product_name,
                aspect_ratio=aspect_ratio,
                music_genre=genre,
                voice_name=voice,
                scenes=[
                    Scene(
                        scene_id=1,
                        title="The Hook",
                        duration=3.5,
                        voice_script=hook_script,
                        visual_prompt=f"cinematic dramatic opening shot of {product_name}, 8k, volumetric lighting, photorealistic, futuristic dark atmosphere",
                        motion_type="zoom_in"
                    ),
                    Scene(
                        scene_id=2,
                        title="The Problem",
                        duration=4.0,
                        voice_script="Traditional tools are clunky, slow, and full of friction. You deserve something better.",
                        visual_prompt=f"chaotic cluttered software interface vs sleek dark minimal design, glowing neon accents, 8k",
                        motion_type="pan_right"
                    ),
                    Scene(
                        scene_id=3,
                        title="The Solution",
                        duration=4.5,
                        voice_script=solution_script,
                        visual_prompt=f"sleek glowing 3D smartphone displaying modern UI for {product_name}, Unreal Engine 5 render, cinematic depth of field",
                        motion_type="zoom_in"
                    ),
                    Scene(
                        scene_id=4,
                        title="The Payoff",
                        duration=3.5,
                        voice_script=cta_script,
                        visual_prompt=f"epic cinematic hero shot, glowing sunset horizon, sleek futuristic tech, 8k masterpiece",
                        motion_type="zoom_out"
                    )
                ]
            )

            return await build_openmontage_video(
                plan=plan,
                topic=product_name,
                aspect_ratio=aspect_ratio,
                voice=voice,
                music_genre=genre,
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
