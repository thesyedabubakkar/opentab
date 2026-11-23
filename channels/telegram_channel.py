import logging
from pathlib import Path
from typing import Optional
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
from core.config import settings
from core.agent_loop import AgentEngine
from channels.base import BaseChannel

logger = logging.getLogger(__name__)

class TelegramChannel(BaseChannel):
    def __init__(self, engine: AgentEngine):
        self.engine = engine
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
            "👋 **Hi! I'm OpenTab, your personal autonomous assistant.**\n\n"
            "Just text me like you would a real assistant. I can:\n"
            "• Search the web and gather live information\n"
            "• Browse websites, interact with pages, and take screenshots\n"
            "• Run data calculations and date math\n"
            "• Remember your preferences and favorite choices\n\n"
            "_What can I do for you today?_"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    async def _on_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = (
            "🛠 **OpenTab Commands:**\n"
            "/start - Welcome screen\n"
            "/help - List commands\n\n"
            "💡 Simply ask any real-world request:\n"
            "• 'Find the top 3 hotels near Central Park and show me pictures'\n"
            "• 'Check https://news.ycombinator.com and tell me what is #1'\n"
            "• 'Remember that I am vegetarian'"
        )
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

    async def _on_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        session_id = f"tg_{chat_id}"
        user_text = update.message.text

        await update.effective_chat.send_action(ChatAction.TYPING)

        try:
            result = await self.engine.handle_message(session_id=session_id, user_text=user_text)

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
                await update.message.reply_text(summary, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

            else:
                reply_text = result.get("content", "Done.")
                await update.message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)

                # Send screenshots if any were taken
                for shot_path in result.get("screenshots", []):
                    if Path(shot_path).exists():
                        with open(shot_path, "rb") as f:
                            await update.message.reply_photo(photo=f, caption="📸 Web View Screenshot")

                # Send AI Generated Images
                for img_path in result.get("images", []):
                    if Path(img_path).exists():
                        with open(img_path, "rb") as f:
                            await update.message.reply_photo(photo=f, caption="🎨 AI Generated Image")

                # Send Videos (Browser action recording or AI generated)
                for vid_path in result.get("videos", []):
                    if Path(vid_path).exists():
                        with open(vid_path, "rb") as f:
                            await update.message.reply_video(video=f, caption="🎬 Video Recording / Generation")

                # Send Voice Notes
                for voice_path in result.get("voices", []):
                    if Path(voice_path).exists():
                        with open(voice_path, "rb") as f:
                            await update.message.reply_voice(voice=f, caption="🎙️ Voice Note")

        except Exception as e:
            logger.error(f"Error handling Telegram message: {e}", exc_info=True)
            await update.message.reply_text(f"⚠️ Error: {str(e)}")

    async def _on_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        data = query.data or ""
        if data.startswith("appr:"):
            _, approval_id, val = data.split(":")
            approved = (val == "1")

            status_str = "Approved ✅" if approved else "Rejected ❌"
            await query.edit_message_text(f"{query.message.text}\n\n**Action {status_str}**", parse_mode=ParseMode.MARKDOWN)

            res = await self.engine.resume_approval(approval_id=approval_id, approved=approved)
            reply_text = res.get("content", "Action processed.")
            await query.message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)
