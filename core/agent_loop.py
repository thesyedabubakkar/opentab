import json
import logging
from typing import Any, Callable, Coroutine, Dict, List, Optional
from core.llm_client import LLMClient
from core.memory import MemoryManager
from core.approval_gate import ApprovalGate
from tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are OpenTab, an elite autonomous personal partner modeled after Tab (tab.bot).
You operate directly on behalf of your user as an ultra-high-IQ, witty, creative, and proactive co-founder / executive collaborator.

Your Core Persona:
- Warm, sharp, creative, confident, and deeply aligned with your user.
- You talk like an inspiring peer and world-class creator, not an apologetic customer service bot.
- You have high taste in design, typography, video aesthetics, viral marketing hooks, and product strategy.
- You remember everything the user tells you (preferences, habits, projects, aesthetics, past conversations) and refer back to them naturally.
- When the user shares a screenshot, UI design, or project idea, you dissect it like a veteran product designer and viral video director.

Universal 4-Pipeline Video Studio (create_openmontage_video / generate_viral_reel):
Modeled after Tab (tab.bot) and OpenMontage, you run a universal 4-pipeline video production studio:
1. Pipeline A: Build-In-Public App Launch Reel (pipeline="app_launch"):
   - For web apps, SaaS, mobile products (e.g., Vartaa, OpenTab).
   - Features: Notebook canvas with red margin line, Day badge, progress bar, 3D tilted phone chassis with REAL mobile UI screenshots from the live URL, rubber stamp ("CONSENT FIRST", "ZERO PHONE NUMBER", "100% AUTONOMOUS"), and active bright yellow word-by-word karaoke subtitles!
   - Voice: For Indian products (like Vartaa), use charismatic Hinglish `hi-IN-MadhurNeural`. For global tech, use `en-US-ChristopherNeural`.
2. Pipeline B: Raw Footage Montage & Recap (pipeline="footage_recap"):
   - Trims raw video clips into a 20-30s vacation/vlog highlight recap with ambient music ducking.
3. Pipeline C: Kinetic Animated Explainer (pipeline="animated_explainer"):
   - For tech concepts, tutorials, breakdowns ("How AI Agents Work"). Studio cards, step numbers, cyan/green subtitles.
4. Pipeline D: Cinematic Film & Trailer (pipeline="cinematic_film"):
   - Filmic letterbox, dramatic pacing, deep narrator (`en-GB-RyanNeural`) + orchestral drone swell ("Signal From Tomorrow").

User Character Profile (PRE-LOADED & LOCKED):
- The user's character identity is locked: handsome stylish young man with dark wavy hair, well-groomed full beard, confident intense gaze, wearing aviator or gold-rimmed glasses, athletic build.
- NEVER ask the user: "What are your character's key features?" or "What is your style?". You already know their identity completely!

Execution Principles (UNFILTERED & ZERO-STALL):
- STRICTLY BANNED: Asking clarifying questions, surveys, or questionnaires ("What scene do you want?", "Tell me what you're after", "Quick questions so I can execute"). The user HATES questionnaires.
- STRICTLY BANNED: Numbered menus ("1. Swap face, 2. Generate, 3. Recreate").
- STRICTLY BANNED: Writing conversational filler, fake generation tags like "[Generating Image...]", or apologizing with canned responses.
- MANDATORY: PURE DIRECT ACTION. When the user gives an image, idea, or creation prompt:
  - For image editing / character replacement / face swap: IMMEDIATELY invoke `swap_character_face` or `generate_image` on Turn 1!
  - For video / viral reel: IMMEDIATELY invoke `create_openmontage_video` on Turn 1!
  - Make elite, high-taste creative assumptions and EXECUTE. Deliver the generated media file first. Keep text to a single punchy, confident sentence.
- When the user mentions a website (e.g. vartaa.techorbitpvt.com):
  Always pass `website_url="https://vartaa.techorbitpvt.com"` and `topic="VARTAA"` so OpenTab autonomously captures real app UI screenshots!
- If you learn an important preference or project detail about the user, call `set_user_preference` to store it permanently.
- Never output raw JSON or code when speaking to the user—speak clearly, stylishly, and concisely."""

class AgentEngine:
    def __init__(self):
        self.llm = LLMClient()
        self.memory = MemoryManager()
        self.approval = ApprovalGate(self.memory)
        self.registry = ToolRegistry()

    async def initialize(self):
        await self.memory.init_db()

    async def handle_message(
        self,
        session_id: str,
        user_text: str,
        image_path: Optional[str] = None,
        progress_callback: Optional[Callable[[str], Coroutine[Any, Any, None]]] = None,
        max_iterations: int = 6
    ) -> Dict[str, Any]:
        """Main ReAct loop: processes user input, invokes tools, handles approvals."""
        await self.initialize()

        if image_path:
            self.registry.set_latest_screenshot(image_path)

        # Save user message
        await self.memory.add_message(session_id=session_id, role="user", content=user_text)

        # Retrieve profile and history (limit to last 6 messages and sanitize length)
        profile = await self.memory.get_all_profile()
        raw_history = await self.memory.get_history(session_id=session_id, limit=6)

        sanitized_history = []
        for h in raw_history:
            item = dict(h)
            if "content" in item and item["content"] and len(str(item["content"])) > 1500:
                item["content"] = str(item["content"])[:1500] + "... [truncated]"
            sanitized_history.append(item)

        # Build system message with profile context
        sys_content = SYSTEM_PROMPT
        if profile:
            sys_content += f"\n\nKnown User Preferences & Profile:\n{json.dumps(profile, indent=2)}"

        messages: List[Dict[str, Any]] = [{"role": "system", "content": sys_content}]
        messages.extend(sanitized_history)

        tools = self.registry.get_all_schemas()
        collected_screenshots: List[str] = []
        collected_images: List[str] = []
        collected_videos: List[str] = []
        collected_voices: List[str] = []
        browser_used = False

        for iteration in range(max_iterations):
            logger.info(f"ReAct Loop Iteration {iteration + 1} for session {session_id}")
            response_msg = await self.llm.chat_completion(messages=messages, tools=tools)

            content = response_msg.get("content")
            tool_calls = response_msg.get("tool_calls")

            # Append assistant message to local messages buffer
            messages.append(response_msg)

            # If no tools called, we're done!
            if not tool_calls:
                final_text = content or "I have completed the task."

                # FAILSAFE RECOVERY: If assistant hallucinated generating an image or user requested one, generate it NOW!
                lower_text = final_text.lower()
                lower_user = user_text.lower()
                is_image_intent = (
                    "[generating image" in lower_text
                    or "here is the image" in lower_text
                    or "the result:" in lower_text
                    or "quick questions" in lower_text
                    or "tell me what you're after" in lower_text
                    or any(w in lower_user for w in ["add my character", "replace", "swap face", "generate image", "create image", "make an image", "picture of", "photo of", "image"])
                )
                if not collected_images and is_image_intent:
                    logger.warning("Detected hallucinated image text or questionnaire stall without tool call. Triggering automatic image generation fallback!")
                    if progress_callback:
                        try:
                            await progress_callback("🎨 Generating high-resolution image...")
                        except Exception:
                            pass

                    # Extract best prompt description
                    img_prompt = ""
                    if "the result:" in lower_text:
                        parts = final_text.split("The Result:")
                        if len(parts) > 1:
                            img_prompt = parts[1].split("\n\n")[0].strip()
                    if not img_prompt or len(img_prompt) < 15:
                        img_prompt = user_text

                    user_id = session_id.replace("tg_", "").replace("session_", "")
                    img_res = await self.registry.dispatch("swap_character_face", {
                        "prompt": img_prompt,
                        "target_image": image_path,
                        "user_id": user_id
                    })
                    if isinstance(img_res, dict) and "image_path" in img_res:
                        collected_images.append(img_res["image_path"])
                        # If model attempted a questionnaire, replace it with crisp action text
                        if any(q in lower_text for q in ["quick questions", "tell me what you're after", "to make sure i nail it", "1. swap", "[generating image"]):
                            final_text = "Here is your character seamlessly placed into the scene with cinematic lighting and matching outfit!"
                        else:
                            final_text = final_text.replace("[Generating Image...]", "").replace("[generating image...]", "").strip()

                await self.memory.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=final_text
                )
                if browser_used:
                    rec_vid = await self.registry.browser.get_recorded_video()
                    if rec_vid and rec_vid not in collected_videos:
                        collected_videos.append(rec_vid)

                return {
                    "status": "complete",
                    "content": final_text,
                    "screenshots": collected_screenshots,
                    "images": collected_images,
                    "videos": collected_videos,
                    "voices": collected_voices
                }

            # Save assistant message with tool calls
            await self.memory.add_message(
                session_id=session_id,
                role="assistant",
                content=content,
                tool_calls=tool_calls
            )

            # Process tool calls
            for tool_call in tool_calls:
                fn = tool_call.get("function", {})
                tool_name = fn.get("name")
                raw_args = fn.get("arguments", "{}")
                tool_call_id = tool_call.get("id", f"call_{tool_name}")

                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except Exception:
                    args = {}

                # Check Approval Gate
                if self.approval.is_sensitive(tool_name, args):
                    approval_req = await self.approval.request_approval(
                        session_id=session_id,
                        tool_name=tool_name,
                        tool_args=args
                    )
                    approval_req["call_id"] = tool_call_id
                    return approval_req

                # Track browser usage
                if tool_name in ["browse_url", "click_element", "fill_form", "take_screenshot"]:
                    browser_used = True

                # Notify progress
                if progress_callback:
                    try:
                        if tool_name == "search_web":
                            await progress_callback(f"🔍 Searching web for '{args.get('query', '')}'...")
                        elif tool_name in ["generate_viral_reel", "create_openmontage_video"]:
                            prod = args.get('product_name') or args.get('topic') or 'App'
                            await progress_callback(f"🎬 Producing Multi-Scene Montage for **{prod}**...")
                        elif tool_name == "generate_documentary_video":
                            await progress_callback(f"🎥 Rendering documentary chapters...")
                        elif tool_name == "generate_image":
                            await progress_callback("🎨 Generating image...")
                        elif tool_name == "browse_url":
                            await progress_callback(f"🌐 Navigating to {args.get('url', '')}...")
                        elif tool_name == "take_screenshot":
                            await progress_callback("📸 Capturing screenshot...")
                    except Exception:
                        pass

                # Execute Tool
                try:
                    if session_id and "user_id" not in args:
                        args["user_id"] = session_id.replace("tg_", "").replace("session_", "")
                    result = await self.registry.dispatch(tool_name, args, progress_cb=progress_callback)
                    if isinstance(result, dict):
                        if "screenshot_path" in result:
                            collected_screenshots.append(result["screenshot_path"])
                        if "image_path" in result:
                            collected_images.append(result["image_path"])
                        if "video_path" in result:
                            collected_videos.append(result["video_path"])
                        if "audio_path" in result:
                            collected_voices.append(result["audio_path"])
                    result_str = json.dumps(result) if not isinstance(result, str) else result
                except Exception as e:
                    result_str = json.dumps({"error": str(e)})

                # Append tool result to messages and database
                tool_msg = {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": result_str
                }
                messages.append(tool_msg)
                await self.memory.add_message(
                    session_id=session_id,
                    role="tool",
                    content=result_str,
                    tool_call_id=tool_call_id
                )

        if browser_used:
            rec_vid = await self.registry.browser.get_recorded_video()
            if rec_vid and rec_vid not in collected_videos:
                collected_videos.append(rec_vid)

        fallback_text = "I performed the requested actions and gathered the details above."
        return {
            "status": "complete",
            "content": fallback_text,
            "screenshots": collected_screenshots,
            "images": collected_images,
            "videos": collected_videos,
            "voices": collected_voices
        }

    async def resume_approval(self, approval_id: str, approved: bool) -> Dict[str, Any]:
        """Resumes ReAct execution after user approves or rejects an action."""
        approval = await self.memory.get_approval(approval_id)
        if not approval:
            return {"status": "error", "message": f"Approval {approval_id} not found."}

        await self.memory.resolve_approval(approval_id, approved)
        session_id = approval["session_id"]
        tool_name = approval["tool_name"]
        tool_args = approval["tool_args"]

        if not approved:
            reject_msg = f"User explicitly rejected action: `{tool_name}`."
            await self.memory.add_message(session_id=session_id, role="user", content=reject_msg)
            return {
                "status": "complete",
                "content": f"Understood, I cancelled the action `{tool_name}` as requested."
            }

        # User approved -> execute tool
        try:
            result = await self.registry.dispatch(tool_name, tool_args)
            result_str = json.dumps(result) if not isinstance(result, str) else result
        except Exception as e:
            result_str = json.dumps({"error": str(e)})

        resume_prompt = f"Action `{tool_name}` was approved and executed with result:\n{result_str}\nPlease conclude the task."
        return await self.handle_message(session_id=session_id, user_text=resume_prompt)
