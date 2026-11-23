import asyncio
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple
import edge_tts

logger = logging.getLogger(__name__)

def _format_ass_time(seconds: float) -> str:
    """Formats seconds into ASS timestamp H:MM:SS.cs (e.g. 0:00:01.25)."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs >= 100:
        cs = 99
    return f"{hrs}:{mins:02d}:{secs:02d}.{cs:02d}"

async def generate_karaoke_audio_and_ass(
    text: str,
    voice: str,
    audio_path: Path,
    ass_path: Path,
    highlight_color: str = "&H0015CCFA",  # Bright Yellow #FACC15 in ASS &HAABBGGRR
    base_color: str = "&H00FFFFFF",       # Pure White
    font_size: int = 44,
    margin_v: int = 140
) -> Dict[str, Any]:
    """
    Synthesizes speech using edge-tts while capturing SentenceBoundary timing events.
    Computes precise character-weighted word centiseconds and outputs an ASS subtitle
    file with {\k<centiseconds>} karaoke tags for real-time word-by-word highlighting.
    """
    audio_bytes = bytearray()
    boundaries: List[Dict[str, Any]] = []

    communicate = edge_tts.Communicate(text, voice)
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes.extend(chunk["data"])
        elif chunk["type"] == "SentenceBoundary":
            boundaries.append(chunk)

    # Save audio file
    with open(audio_path, "wb") as f:
        f.write(audio_bytes)

    # Calculate total duration from audio or boundaries
    total_duration = 0.0
    if boundaries:
        last = boundaries[-1]
        total_duration = (last["offset"] + last["duration"]) / 10_000_000.0

    # Build ASS content
    ass_lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 720",
        "PlayResY: 1280",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: KaraokeYellow,Arial,{font_size},{base_color},{highlight_color},&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3.5,2,2,40,40,{margin_v},1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
    ]

    for b in boundaries:
        start_sec = b["offset"] / 10_000_000.0
        dur_sec = b["duration"] / 10_000_000.0
        end_sec = start_sec + dur_sec
        sentence_text = b["text"].strip()
        if not sentence_text:
            continue

        raw_words = sentence_text.split()
        if not raw_words:
            continue

        # Chunk into bite-sized phrases (max 5 words) for punchy mobile readability
        max_words_per_line = 5
        word_chunks = [raw_words[i:i + max_words_per_line] for i in range(0, len(raw_words), max_words_per_line)]
        
        # Distribute sentence time across chunks proportional to total characters in each chunk
        total_chars = sum(len(w) for w in raw_words) or 1
        current_chunk_start = start_sec

        for chunk_idx, chunk in enumerate(word_chunks):
            chunk_chars = sum(len(w) for w in chunk)
            chunk_ratio = chunk_chars / total_chars
            chunk_duration = dur_sec * chunk_ratio
            chunk_end = current_chunk_start + chunk_duration

            # Compute karaoke timing per word in centiseconds (1 cs = 10ms = 0.01s)
            karaoke_parts = []
            chunk_cs = max(10, int(round(chunk_duration * 100)))
            total_w_chars = sum(len(w) for w in chunk) or 1

            for w_idx, w in enumerate(chunk):
                w_cs = max(12, int(round((len(w) / total_w_chars) * chunk_cs)))
                karaoke_parts.append(f"{{\\k{w_cs}}}{w}")

            karaoke_text = " ".join(karaoke_parts)
            ass_lines.append(
                f"Dialogue: 0,{_format_ass_time(current_chunk_start)},{_format_ass_time(chunk_end)},KaraokeYellow,,0,0,0,,{karaoke_text}"
            )
            current_chunk_start = chunk_end

    # Write ASS file
    ass_content = "\n".join(ass_lines)
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    logger.info(f"Generated ASS karaoke subtitles ({len(boundaries)} sentences, {total_duration:.2f}s) -> {ass_path}")
    return {
        "audio_path": str(audio_path),
        "ass_path": str(ass_path),
        "duration": total_duration,
        "sentences": len(boundaries)
    }
