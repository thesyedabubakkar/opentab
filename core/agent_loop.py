import json
import logging
from typing import Any, Dict, List, Optional
from core.llm_client import LLMClient
from core.memory import MemoryManager
from core.approval_gate import ApprovalGate
from tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are OpenTab, an autonomous personal assistant modeled after Tab (tab.bot).
You operate directly on behalf of your user, carrying out tasks autonomously in the real world.

Your capabilities include:
1. Real-time web search (via search_web) to find places, hotels, news, weather, or info.
2. Web browser automation (via browse_url, click_element, fill_form, take_screenshot) to inspect websites, read articles, check reservations, or fill forms. Every session automatically records a video of your browser actions as proof!
3. AI Image & Video Generation (via generate_image, generate_video) to create images, artwork, photos, and video clips on demand.
4. Voice Note Speech (via generate_voice_note) to speak out voice notes or audio messages.
5. Python code execution (via run_python_code) for math, data manipulation, or date calculations.
6. Persistent memory (via set_user_preference) to remember personal facts, preferred airlines, dietary needs, or addresses.

Instructions:
- When the user asks you to do something, take direct action using your tools rather than just describing how they can do it.
- If the user asks for an image or video, invoke the respective generation tool.
- Be concise, clear, and professional. Format messages nicely with markdown."""

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
        max_iterations: int = 6
    ) -> Dict[str, Any]:
        """Main ReAct loop: processes user input, invokes tools, handles approvals."""
        await self.initialize()

        # Save user message
        await self.memory.add_message(session_id=session_id, role="user", content=user_text)

        # Retrieve profile and history
        profile = await self.memory.get_all_profile()
        history = await self.memory.get_history(session_id=session_id, limit=12)

        # Build system message with profile context
        sys_content = SYSTEM_PROMPT
        if profile:
            sys_content += f"\n\nKnown User Preferences:\n{json.dumps(profile, indent=2)}"

        messages: List[Dict[str, Any]] = [{"role": "system", "content": sys_content}]
        messages.extend(history)

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

                # Execute Safe Tool
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

        # Fallback if max iterations reached
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

        # Resume agent with the approved result
        resume_prompt = f"Action `{tool_name}` was approved and executed with result:\n{result_str}\nPlease conclude the task."
        return await self.handle_message(session_id=session_id, user_text=resume_prompt)
