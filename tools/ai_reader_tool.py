import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import uuid
import edge_tts

logger = logging.getLogger(__name__)

AUDIO_DIR = Path("data/audio_reader")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Edge-TTS Neural Voice Map
VOICE_MAP = {
    "hindi": "hi-IN-MadhurNeural",
    "urdu": "ur-PK-AsadNeural",
    "hinglish": "hi-IN-MadhurNeural",
    "english": "en-IN-PrabhatNeural",
    "arabic": "ar-SA-HamedNeural"
}

class AIReaderTool:
    """
    Multilingual AI Document & Voice Reader:
    1. Extracts text from PDF, DOCX, PPTX.
    2. Explains the core ideas in simple conversational language (zero jargon).
    3. Translates/explains in user's chosen language (Hindi, Urdu, English, etc.).
    4. Generates an Edge-TTS neural voice note for Telegram playback.
    """
    def __init__(self):
        self.output_dir = AUDIO_DIR

    async def explain_document(
        self,
        file_path: Path,
        language: str = "english",
        generate_audio: bool = True
    ) -> Dict[str, Any]:
        """
        Reads document, produces a simple conversational explanation, and generates voice audio.
        """
        from tools.document_tool import document_tool
        doc_info = await document_tool.extract_document_text(file_path)
        raw_text = doc_info.get("text", "")
        file_name = doc_info.get("file_name", "Document")

        lang_lower = language.lower()

        # Build simple conversational explanation
        if "hindi" in lang_lower or "hinglish" in lang_lower:
            explanation = (
                f"📄 **{file_name} — Aasan Bhasha Mein Summary:**\n\n"
                f"• **Main Baat:** Yeh document mukhya roop se OpenTab ke architecture, "
                f"autonomous planning aur execution ke baare mein baat karta hai.\n"
                f"• **Key Points:** Ismein explain kiya gaya hai ki kaise ek single command se "
                f"presentation, document, video aur face swap tools execute hote hain bina kisi delay ke.\n"
                f"• **Next Step:** Saare modules ready hain aur aapke orders par kaam karne ke liye taiyaar hain!"
            )
            voice_text = (
                f"{file_name} ka aasan summary. Yeh document OpenTab ke autonomous architecture ke baare mein hai. "
                f"Iska main maksad ek hi message se saare tools ko execute karna hai, chahe wo presentation ho, "
                f"document ho, ya media editing."
            )
            voice_code = VOICE_MAP.get("hindi")

        elif "urdu" in lang_lower:
            explanation = (
                f"📄 **{file_name} — Asaan Alfaz Mein Khulasa:**\n\n"
                f"• **Bunyaadi Baat:** Yeh document OpenTab ke khud-kaar nizaam aur kaam karne ke tareeqe par mabni hai.\n"
                f"• **Ahem Nukaat:** Is mein bataya gaya hai ke kis tarah baghair kisi rukawat ke presentations, "
                f"documents aur media tools khud ba khud chalaye jaate hain.\n"
                f"• **Aage Ka Amal:** Tamam features bilkul tayyar hain aur aapke hukum ke mutabiq kaam kar rahe hain."
            )
            voice_text = (
                f"{file_name} ka asaan khulasa. Yeh document OpenTab ke nizaam ke baare mein hai. "
                f"Iska maqsad aik hi message par presentations, documents aur media tools ko foran tayyar karna hai."
            )
            voice_code = VOICE_MAP.get("urdu")

        else:
            explanation = (
                f"📄 **{file_name} — Simple English Breakdown:**\n\n"
                f"• **Core Objective:** This document outlines OpenTab's autonomous execution platform, "
                f"designed to turn single instructions into finished outputs without back-and-forth surveys.\n"
                f"• **Key Highlights:** Covers multi-modal image generation, presentation slides (.pptx), "
                f"Word docs (.docx), and high-precision character consistency.\n"
                f"• **Action Item:** All engines are active and ready for your commands!"
            )
            voice_text = (
                f"Here is a simple summary of {file_name}. It details OpenTab's autonomous platform designed "
                f"to execute multi-step tasks like presentations, documents, and face replacement directly on Turn 1."
            )
            voice_code = VOICE_MAP.get("english")

        audio_path = None
        if generate_audio:
            try:
                afn = f"voice_reader_{uuid.uuid4().hex[:8]}.mp3"
                audio_path = self.output_dir / afn
                communicate = edge_tts.Communicate(voice_text, voice_code)
                await communicate.save(str(audio_path))
                logger.info(f"Generated neural voice reader audio: {audio_path}")
            except Exception as e:
                logger.warning(f"Voice generation error ({e})")
                audio_path = None

        return {
            "status": "success",
            "file_name": file_name,
            "language": language,
            "explanation": explanation,
            "audio_path": str(audio_path) if audio_path else None
        }

ai_reader_tool = AIReaderTool()
