import asyncio
import logging
from typing import Optional
from aiohttp import web
import httpx
from core.config import settings
from core.agent_loop import AgentEngine
from channels.base import BaseChannel

logger = logging.getLogger(__name__)

class WhatsAppBridge(BaseChannel):
    def __init__(self, engine: AgentEngine):
        self.engine = engine
        self.port = settings.PORT
        self.node_service_url = f"http://localhost:{settings.WHATSAPP_PORT}/send"
        self._runner: Optional[web.AppRunner] = None
        self._pending_approvals = {}  # sender -> approval_id

    async def start(self):
        app = web.Application()
        app.router.add_get("/", self._handle_health)
        app.router.add_get("/health", self._handle_health)
        app.router.add_post("/webhook/whatsapp", self._handle_webhook)

        self._runner = web.AppRunner(app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, "0.0.0.0", self.port)
        await site.start()
        logger.info(f"OpenTab HTTP server & webhook listening on port {self.port}...")

    async def _handle_health(self, request: web.Request) -> web.Response:
        return web.json_response({
            "status": "healthy",
            "agent": settings.AGENT_NAME,
            "version": "1.0.0",
            "llm_provider": settings.LLM_PROVIDER
        })

    async def stop(self):
        if self._runner:
            await self._runner.cleanup()

    async def send_message(
        self,
        session_id: str,
        text: str,
        image_path: Optional[str] = None,
        video_path: Optional[str] = None,
        audio_path: Optional[str] = None
    ):
        """Sends message out via the local Node.js Baileys service."""
        recipient = session_id.replace("wa_", "")
        payload = {"to": recipient, "text": text}
        if image_path:
            payload["image_path"] = image_path
        if video_path:
            payload["video_path"] = video_path
        if audio_path:
            payload["audio_path"] = audio_path

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(self.node_service_url, json=payload)
                return res.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message to {recipient}: {e}")
            return False

    async def _handle_webhook(self, request: web.Request) -> web.Response:
        data = await request.json()
        sender = data.get("sender")
        text = data.get("text", "").strip()

        if not sender or not text:
            return web.json_response({"status": "ignored"})

        session_id = f"wa_{sender}"

        # Handle pending approval response via text (e.g., '1', 'yes', 'approve' / '0', 'no', 'cancel')
        if sender in self._pending_approvals:
            approval_id = self._pending_approvals.pop(sender)
            is_approved = text.lower() in ["1", "yes", "y", "approve", "confirm"]
            is_rejected = text.lower() in ["0", "no", "n", "reject", "cancel"]

            if is_approved or is_rejected:
                res = await self.engine.resume_approval(approval_id, approved=is_approved)
                reply = res.get("content", "Processed.")
                await self.send_message(session_id, reply)
                return web.json_response({"status": "approval_handled"})

        # Normal message processing
        asyncio.create_task(self._process_message(session_id, sender, text))
        return web.json_response({"status": "processing"})

    async def _process_message(self, session_id: str, sender: str, text: str):
        try:
            result = await self.engine.handle_message(session_id=session_id, user_text=text)

            if result.get("status") == "requires_approval":
                approval_id = result["approval_id"]
                self._pending_approvals[sender] = approval_id
                summary = result["summary"]
                prompt = (
                    f"{summary}\n\n"
                    "👉 Reply *1* (or 'yes') to **Approve**\n"
                    "👉 Reply *0* (or 'no') to **Cancel**"
                )
                await self.send_message(session_id, prompt)

            else:
                reply_text = result.get("content", "Done.")
                screenshots = result.get("screenshots", [])
                images = result.get("images", [])
                videos = result.get("videos", [])
                voices = result.get("voices", [])

                # Deliver videos first if any
                if videos:
                    await self.send_message(session_id, reply_text, video_path=videos[0])
                elif images or screenshots:
                    primary_img = images[0] if images else screenshots[0]
                    await self.send_message(session_id, reply_text, image_path=primary_img)
                elif voices:
                    await self.send_message(session_id, reply_text, audio_path=voices[0])
                else:
                    await self.send_message(session_id, reply_text)

        except Exception as e:
            logger.error(f"Error in WhatsApp message processing: {e}", exc_info=True)
            await self.send_message(session_id, f"⚠️ Error: {str(e)}")
