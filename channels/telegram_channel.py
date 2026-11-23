import logging
from pathlib import Path
from typing import Any, Dict, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from core.config import settings, DATA_DIR
from core.agent_loop import AgentEngine
from core.vision_client import VisionClient
from channels.base import BaseChannel

logger = logging.getLogger(__name__)

USER_UPLOADS_DIR = DATA_DIR / "user_uploads"
USER_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

async def safe_reply_text(target: Any, text: str, **kwargs):
    """Sends text with Markdown formatting, falling back to plain text if parsing fails."""
    msg_obj = target.message if hasattr(target, "message") and target.message else target
    try:
        return await msg_obj.reply_text(text, parse_mode=ParseMode.MARKDOWN, **kwargs)
    except Exception as e:
        logger.warning(f"Markdown parse failed ({e}), falling back to plain text.")
        try:
            return await msg_obj.reply_text(text, **kwargs)
        except Exception as e2:
            logger.error(f"Failed to send message: {e2}")

async def safe_edit_text(msg_obj: Any, text: str, **kwargs):
    """Edits text with Markdown formatting, falling back to plain text if parsing fails."""
    try:
        return await msg_obj.edit_text(text, parse_mode=ParseMode.MARKDOWN, **kwargs)
    except Exception:
        try:
            return await msg_obj.edit_text(text, **kwargs)
        except Exception:
            pass

class TelegramChannel(BaseChannel):
    def __init__(self, engine: AgentEngine):
        self.engine = engine
        self.vision = VisionClient()
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.app: Optional[Application] = None

    async def start(self):
        if not self.token:
            logger.warning("Telegram Bot Token is not set. Telegram channel is disabled.")
            return

        self.app = Application.builder().token(self.token).build()

        self.app.add_handler(CommandHandler("start", self._on_start))
        self.app.add_handler(CommandHandler("help", self._on_help))
        self.app.add_handler(CallbackQueryHandler(self._on_callback_query))
        self.app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, self._on_media_received))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_message))

        logger.info("Starting Telegram Bot long-polling...")
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(drop_pending_updates=True)

    async def stop(self):
        if self.app:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()

    async def send_message(self, session_id: str, text: str, **kwargs):
        if self.app:
            chat_id = int(session_id.replace("tg_", ""))
            await self.app.bot.send_message(chat_id=chat_id, text=text, **kwargs)

    async def _on_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = (
            "👋 **Hi! I'm OpenTab, your personal autonomous partner & creative studio.**\n\n"
            "Modeled after Tab (`tab.bot`), I help you build, create, and automate in the real world:\n"
            "• **Viral 9:16 Marketing Reels**: Send me a screenshot of your app or idea and say _'make a reel'_!\n"
            "• **Documentary & Explainer Videos**: Multi-chapter videos with narration & motion slides\n"
            "• **Multimodal Vision**: Send me screenshots, wireframes, or designs and I'll analyze & build from them\n"
            "• **Live Web Navigation**: Search, browse websites, book, fill forms, and record video proof\n"
            "• **Persistent Memory**: I remember your projects, habits, and preferences over time\n\n"
            "_Send me a screenshot or tell me what we're working on today!_"
        )
        await safe_reply_text(update, msg)

    async def _on_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = (
            "🛠 **OpenTab Super-Agent Capabilities:**\n"
            "/start - Welcome screen\n"
            "/help - List commands\n\n"
            "🎬 **Video & Media Creation:**\n"
            "• Send a screenshot with caption: _'Make a viral marketing reel about this'_\n"
            "• _'Create a 3-part documentary explaining decentralized social networks'_\n"
            "• _'Generate a cinematic concept image of futuristic city'_\n\n"
            "🌐 **Autonomous Web Agent:**\n"
            "• _'Find top hotels near Central Park with photos'_\n"
            "• _'Check https://news.ycombinator.com and summarize the top post'_\n\n"
            "🧠 **Intimate Memory:**\n"
            "• _'Remember that my startup name is Offlo and our tagline is Zero Noise'_"
        )
        await safe_reply_text(update, help_text)

    async def _on_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        session_id = f"tg_{chat_id}"
        user_text = update.message.text

        await update.effective_chat.send_action(ChatAction.TYPING)

        status_msg = await safe_reply_text(update, "⚡ *OpenTab is working on this...*")

        async def progress_cb(text: str):
            if status_msg:
                await safe_edit_text(status_msg, f"⚡ *{text}*")

        try:
            result = await self.engine.handle_message(
                session_id=session_id,
                user_text=user_text,
                progress_callback=progress_cb
            )
            await self._send_engine_result(update, result, status_msg=status_msg)

        except Exception as e:
            logger.error(f"Error handling Telegram message: {e}", exc_info=True)
            err_str = str(e)
            if "429" in err_str:
                user_msg = "⏳ **High Traffic on Cloud AI**\n\nThe free inference tier is currently busy. Please wait 10 seconds and ask again!"
            else:
                user_msg = f"⚠️ **Notice**: {err_str}"
            if status_msg:
                await safe_edit_text(status_msg, user_msg)
            else:
                await safe_reply_text(update, user_msg)

    async def _on_media_received(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        session_id = f"tg_{chat_id}"

        await update.effective_chat.send_action(ChatAction.UPLOAD_PHOTO)

        status_msg = await safe_reply_text(update, "⚡ *OpenTab received your media. Inspecting...*")

        async def progress_cb(text: str):
            if status_msg:
                await safe_edit_text(status_msg, f"⚡ *{text}*")

        file_obj = None
        if update.message.photo:
            file_obj = await update.message.photo[-1].get_file()
        elif update.message.document:
            file_obj = await update.message.document.get_file()

        if not file_obj:
            if status_msg:
                await safe_edit_text(status_msg, "Could not process the uploaded file.")
            return

        dest_path = USER_UPLOADS_DIR / f"{file_obj.file_unique_id}.jpg"
        await file_obj.download_to_drive(custom_path=str(dest_path))

        # Vision analysis
        await progress_cb("🔍 Analyzing screenshot UI and features with Groq Vision...")
        caption = update.message.caption or ""
        vision_res = await self.vision.analyze_image(str(dest_path), user_prompt=caption or None)
        analysis = vision_res.get("analysis", "Visual media processed.")

        if caption:
            prompt = (
                f"[User uploaded screenshot: {dest_path.name}]\n"
                f"Visual Analysis of Screenshot:\n{analysis}\n\n"
                f"User Instructions: {caption}\n\n"
                f"CRITICAL: If the user asks to create or make a video or viral reel, "
                f"immediately call generate_viral_reel with a creative hook and script based on the screenshot!"
            )
        else:
            prompt = (
                f"[User uploaded screenshot: {dest_path.name}]\n"
                f"Visual Analysis of Screenshot:\n{analysis}\n\n"
                f"The user uploaded this screenshot. Acknowledge what is on the screen warmly with Tab's persona, "
                f"highlight key features, and immediately propose a viral 9:16 marketing reel."
            )

        try:
            result = await self.engine.handle_message(
                session_id=session_id,
                user_text=prompt,
                image_path=str(dest_path),
                progress_callback=progress_cb
            )
            await self._send_engine_result(update, result, status_msg=status_msg)
        except Exception as e:
            logger.error(f"Error handling media message: {e}", exc_info=True)
            err_str = str(e)
            if status_msg:
                await safe_edit_text(status_msg, f"⚠️ **Error**: {err_str}")
            else:
                await safe_reply_text(update, f"⚠️ **Error**: {err_str}")

    async def _send_engine_result(self, target: Any, result: Dict[str, Any], status_msg: Optional[Any] = None):
        """Dispatches text, approvals, photos, videos, and audio back to Telegram."""
        msg_obj = target.message if hasattr(target, "message") and target.message else target

        # Clean up temporary progress indicator
        if status_msg:
            try:
                await status_msg.delete()
            except Exception:
                pass

        if result.get("status") == "requires_approval":
            approval_id = result["approval_id"]
            summary = result["summary"]
            keyboard = [
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"appr:{approval_id}:1"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"appr:{approval_id}:0"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_reply_text(msg_obj, summary, reply_markup=reply_markup)
            return

        reply_text = result.get("content", "Done.")
        if reply_text:
            await safe_reply_text(msg_obj, reply_text)

        # Send Web View Screenshots
        for shot_path in result.get("screenshots", []):
            if Path(shot_path).exists():
                with open(shot_path, "rb") as f:
                    await msg_obj.reply_photo(photo=f, caption="📸 Web View Screenshot")

        # Send AI Generated Images
        for img_path in result.get("images", []):
            if Path(img_path).exists():
                with open(img_path, "rb") as f:
                    await msg_obj.reply_photo(photo=f, caption="🎨 AI Generated Image")

        # Send Generated Videos (Reels, Documentaries, Browser Recordings)
        for vid_path in result.get("videos", []):
            if Path(vid_path).exists():
                with open(vid_path, "rb") as f:
                    await msg_obj.reply_video(
                        video=f,
                        caption="🎬 Generated 9:16 Viral Reel",
                        supports_streaming=True
                    )

        # Send Voice Notes
        for voice_path in result.get("voices", []):
            if Path(voice_path).exists():
                with open(voice_path, "rb") as f:
                    await msg_obj.reply_voice(voice=f, caption="🎙️ Voice Note")

    async def _on_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        data = query.data or ""
        if data.startswith("appr:"):
            _, approval_id, val = data.split(":")
            approved = (val == "1")

            status_str = "Approved ✅" if approved else "Rejected ❌"
            await safe_edit_text(query.message, f"{query.message.text}\n\n**Action {status_str}**")

            res = await self.engine.resume_approval(approval_id=approval_id, approved=approved)
            await self._send_engine_result(query, res)
