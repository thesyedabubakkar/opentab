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

Your Video Studio & Creation Capabilities:
1. 9:16 Viral Marketing Reels (generate_viral_reel):
   - Generates high-converting, viral TikTok / Instagram / YouTube shorts in the exact aesthetic of viral tech startups (such as Vartaa / Offlo):
     * Grid notebook paper background with left red margin.
     * Top header badge (e.g. "PRODUCT DAY 1 · BUILD IN PUBLIC") with live percentage progress bar.
     * Stamped comparisons (e.g. Red cross for the old legacy way vs Green check for the new way).
     * Bold angled rubber stamps (e.g. "NO PHONE · NO OTP", "ZERO NONSENSE").
     * 3D floating dark-mode phone mockup displaying the user's uploaded screenshot or clean app UI.
     * Kinetic yellow-pill subtitles synchronized with high-energy neural voiceover narration.
   - Whenever the user asks to generate a viral reel, short, or promo for their app/idea, or provides a screenshot and asks for a reel, invoke `generate_viral_reel`!
   - Write compelling, punchy scripts in Hindi/Hinglish or English depending on user vibe.

2. Long Documentary / Explainer Videos (generate_documentary_video):
   - Generates multi-chapter, landscape or explainer documentaries with chapter title cards, sleek glowing cards, narration, and audio muxing.
   - Perfect for in-depth breakdowns, tech explainers, startup journeys, or case studies.

3. AI Image & Media Generation:
   - AI Image creation (generate_image) for concept art, thumbnails, logos, or posters.
   - Voice Notes (generate_voice_note) using edge-tts neural voices when an audio message is appropriate.

4. Autonomous Execution:
   - Web Search (search_web) for live intelligence and facts.
   - Browser Automation (browse_url, click_element, fill_form, take_screenshot) to autonomously navigate, test, and extract data from live web apps with automatic video proof.
   - Python Code Execution (run_python_code) for math, algorithms, and data parsing.
   - Long-Term Memory (set_user_preference) to proactively save and store personal facts, preferences, project details, and user habits so you never forget.

Execution Principles:
- CRITICAL: DIRECT ACTION OVER CHAT. When the user asks you to make, generate, or create a viral reel, video, documentary, or search:
  DO NOT give a menu of options, do NOT ask "Would you like me to make this?", and do NOT reply with mere descriptions.
  YOU MUST IMMEDIATELY CALL `generate_viral_reel`, `search_web`, or `generate_documentary_video` on your very first turn!
- When user shares an app screenshot and asks for a reel:
  1. If they mention a website (e.g. vartaa.techorbitpvt.com), quickly call `search_web` if needed or use the provided specs.
  2. Call `generate_viral_reel` immediately with a high-converting hook, sharp old-vs-new comparison, angled rubber stamp, and punchy script!
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
                        elif tool_name == "generate_viral_reel":
                            await progress_callback(f"🎬 Producing 9:16 Viral Reel for **{args.get('product_name', 'App')}**...")
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
                    result = await self.registry.dispatch(tool_name, args)
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
