import json
import logging
import re
from typing import Any, Dict, List, Optional
from core.llm_client import LLMClient
from core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_DIRECTOR_PROMPT = """You are OpenTab's God-Level Video Director, modeled after Claude Code and anything2explainer.
Your job is to transform ANY user prompt or topic into a world-class, 6-9 scene motion-graphics vertical reel (9:16).

STRICT RULE: DO NOT USE RIGID TEMPLATES. Every topic must receive bespoke, custom-designed cards, graphics, diagrams, and narration.

Visual Frameworks:
1. "shor_explainer" (Default for software, AI tools, libraries, startups - matching the viral SHOR style):
   - Header with category badges ("FREE AI FILM STUDIO", "MEET THE TOOL", "3 EASY STEPS", "VIDEO STUDIO", "BOTTOM LINE") and part counters ("PART 01" to "PART 11").
   - Giant embossed background watermark numbers ("01", "02", "05", "07", "09").
   - Mac studio window ("AI Studio REC") with video previews, comparison matrices ("Original" vs "Open Source Free"), step guides, and pricing breakdowns.
   - High-contrast red pill subtitle highlight ("open-source", "mehnge", "free").
   - Bottom checkpoint scrub bar ("P1" to "P11") with a moving ball tracking progress (0-100%).

2. "workflow_breakdown" (For tutorials, coding agents, system pipelines, CPM tricks):
   - Interactive step pills ("1 Claude Code", "2 Voice model", "3 Image model").
   - Live audio waveform visualizers ("Kokoro voice model") and terminal status pills ("Claude: installing... 99%").
   - Comparative bar charts ("India ≈ ₹65" vs "USA ≈ ₹924" CPM).

Output format: You MUST return a single valid JSON object with:
{
  "style": "shor_explainer" or "workflow_breakdown",
  "topic": "Clean Title",
  "scenes": [
    {
      "id": 1,
      "category_tag": "CATEGORY",
      "part_label": "PART 01",
      "watermark_number": "01",
      "card_type": "window_preview" | "comparison_matrix" | "step_guide" | "waveform_spec" | "barchart_comparison" | "pricing_breakdown" | "cta_card",
      "headline": "Big Bold Title",
      "subtext": "Subtitle or context",
      "card_data": { ... component specific values ... },
      "highlight_word": "keyword_to_highlight_in_red_pill",
      "narration_script": "Punchy spoken voiceover in natural Hinglish or English (15-25 words)",
      "progress_percent": 10
    }
  ]
}
"""

class Prompt2VideoDirector:
    def __init__(self):
        self.llm = LLMClient()

    async def direct(self, user_prompt: str, website_url: Optional[str] = None) -> Dict[str, Any]:
        """Synthesizes a bespoke multi-scene storyboard directly from the prompt."""
        clean_prompt = user_prompt.strip()
        if website_url and website_url not in clean_prompt:
            clean_prompt += f" (Website: {website_url})"

        prompt_msg = f"User Request: {clean_prompt}\nGenerate the complete multi-scene JSON storyboard now."

        messages = [
            {"role": "system", "content": SYSTEM_DIRECTOR_PROMPT},
            {"role": "user", "content": prompt_msg}
        ]

        try:
            resp = await self.llm.chat_completion(messages=messages, tools=None)
            raw_content = resp.get("content", "")
            
            # Extract JSON block
            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_content, re.DOTALL)
            json_str = match.group(1) if match else raw_content
            parsed = json.loads(json_str)

            if "scenes" in parsed and len(parsed["scenes"]) >= 4:
                return parsed
        except Exception as e:
            logger.warning(f"LLM video director parsing failed ({e}). Falling back to heuristic director.")

        return self._generate_fallback_storyboard(clean_prompt, website_url)

    def _generate_fallback_storyboard(self, prompt: str, website_url: Optional[str] = None) -> Dict[str, Any]:
        """Reliable heuristic generator when LLM inference is rate-limited."""
        clean_topic = re.sub(r'https?://\S+', '', prompt).replace("Make a video explaining", "").replace("viral reel", "").strip() or "Open Higgsfield AI"
        clean_topic = clean_topic[:30].strip().title()

        is_workflow = any(k in prompt.lower() for k in ["claude", "workflow", "automate", "pipeline", "earn", "cpm", "tips"])

        if is_workflow:
            return {
                "style": "workflow_breakdown",
                "topic": clean_topic,
                "scenes": [
                    {
                        "id": 1,
                        "category_tag": "AUTOMATION HACK",
                        "part_label": "PART 01",
                        "watermark_number": "01",
                        "card_type": "step_guide",
                        "headline": "VIRAL AI VIDEOS",
                        "subtext": "Poora process bilkul free mein",
                        "card_data": {"step_num": "1", "title": "Claude Code Setup", "url": "claude.ai/code", "badge": "100% FREE"},
                        "highlight_word": "free",
                        "narration_script": f"Bhai {clean_topic} se poori viral video bilkul free mein generate kar sakte hain, isliye video ko abhi save kar lo.",
                        "progress_percent": 12
                    },
                    {
                        "id": 2,
                        "category_tag": "PRO TIP",
                        "part_label": "PART 02",
                        "watermark_number": "02",
                        "card_type": "barchart_comparison",
                        "headline": "HIGH CPM STRATEGY",
                        "subtext": "English narration reaches US viewers",
                        "card_data": {"title": "Earnings per 1,000 views", "item1": "India ≈ ₹65", "item2": "USA ≈ ₹924", "ratio": 14},
                        "highlight_word": "revenue",
                        "narration_script": "Aur ek pro tip, agar narration English mein rakhte ho to video US mein chalegi jahan ka revenue bahot tagda milega.",
                        "progress_percent": 35
                    },
                    {
                        "id": 3,
                        "category_tag": "TECH STACK",
                        "part_label": "PART 03",
                        "watermark_number": "03",
                        "card_type": "waveform_spec",
                        "headline": "VOICE & IMAGE ENGINE",
                        "subtext": "Zero subscription required",
                        "card_data": {"tool_name": "Kokoro TTS", "device": "runs on your laptop", "status": "Claude: installing Kokoro... 99%"},
                        "highlight_word": "laptop",
                        "narration_script": "Isme Kokoro voice model tumhare laptop par chalta hai aur images ke liye Flux ya Gemini bilkul free use kar sakte ho.",
                        "progress_percent": 68
                    },
                    {
                        "id": 4,
                        "category_tag": "STEP BY STEP",
                        "part_label": "PART 04",
                        "watermark_number": "04",
                        "card_type": "cta_card",
                        "headline": "DIRECT DM LINK",
                        "subtext": "Comment karo seedha guide milegi",
                        "card_data": {"action_keyword": "CODE", "stamp": "DM SENT"},
                        "highlight_word": "comment",
                        "narration_script": "Iska step by step guide aur prompt file seedha DM mein chahiye to comment mein likho code aur follow karna mat bhoolna.",
                        "progress_percent": 100
                    }
                ]
            }

        # Default SHOR Explainer Format (Matching Reference Video 1)
        return {
            "style": "shor_explainer",
            "topic": clean_topic,
            "scenes": [
                {
                    "id": 1,
                    "category_tag": "FREE AI FILM STUDIO",
                    "part_label": "PART 01",
                    "watermark_number": "01",
                    "card_type": "window_preview",
                    "headline": f"POORA {clean_topic.upper()} STUDIO",
                    "subtext": "40 se zyada AI models ek hi app mein",
                    "card_data": {"window_title": "AI Studio REC", "timecode": "00:00:12", "has_grid": True},
                    "highlight_word": "free",
                    "narration_script": f"Kisi ne abhi poora ka poora AI filmmaking studio bilkul free mein release kar diya hai jiska naam hai {clean_topic}.",
                    "progress_percent": 10
                },
                {
                    "id": 2,
                    "category_tag": "MEET THE TOOL",
                    "part_label": "PART 02",
                    "watermark_number": "02",
                    "card_type": "comparison_matrix",
                    "headline": clean_topic.upper(),
                    "subtext": "Higgsfield original VS Open Source FREE",
                    "card_data": {"left_label": "Original $50/mo", "right_label": "Open Source FREE", "stamp": "</> OPEN SOURCE"},
                    "highlight_word": "open-source",
                    "narration_script": "Isme aapko image generation, video studio aur cinema control sab kuch bina kisi monthly subscription ke milta hai.",
                    "progress_percent": 25
                },
                {
                    "id": 3,
                    "category_tag": "3 EASY STEPS",
                    "part_label": "PART 05",
                    "watermark_number": "05",
                    "card_type": "step_guide",
                    "headline": "GITHUB SE DOWNLOAD",
                    "subtext": "Download karo aur free API connect karo",
                    "card_data": {"step_num": "STEP 1", "title": "GitHub se download", "url": f"github.com/{clean_topic.replace(' ', '')}", "badge": "15%"},
                    "highlight_word": "download",
                    "narration_script": "Chalo dikhati hoon ise setup kaise karna hai, sabse pehle GitHub se download karo aur free key connect kar lo.",
                    "progress_percent": 45
                },
                {
                    "id": 4,
                    "category_tag": "VIDEO STUDIO",
                    "part_label": "PART 07",
                    "watermark_number": "07",
                    "card_type": "window_preview",
                    "headline": "TEXT YA IMAGE SE VIDEO",
                    "subtext": "Realistic camera movement & lighting",
                    "card_data": {"window_title": "VIDEO STUDIO", "timecode": "00:02:18", "has_grid": False},
                    "highlight_word": "realistic",
                    "narration_script": "Video studio mein text ya image se realistic videos bana sakte ho aur camera angles ko pro filmmakers ki tarah control kar sakte ho.",
                    "progress_percent": 70
                },
                {
                    "id": 5,
                    "category_tag": "BOTTOM LINE",
                    "part_label": "PART 09",
                    "watermark_number": "09",
                    "card_type": "pricing_breakdown",
                    "headline": "MAHNGE AI TOOLS KHATAM",
                    "subtext": "Zero cost all-in-one studio",
                    "card_data": {
                        "items": [
                            {"name": "Image tool", "price": "₹₹₹ / month"},
                            {"name": "Video tool", "price": "₹₹₹ / month"},
                            {"name": "Voice tool", "price": "₹₹₹ / month"}
                        ]
                    },
                    "highlight_word": "mehnge",
                    "narration_script": "Yaani mehnge AI tools ka saara kaam ab ek hi free app mein bina kisi monthly billing ke ho jayega.",
                    "progress_percent": 88
                },
                {
                    "id": 6,
                    "category_tag": "GET ACCESS",
                    "part_label": "PART 11",
                    "watermark_number": "11",
                    "card_type": "cta_card",
                    "headline": "DIRECT REPO LINK",
                    "subtext": "Comment karo seedha link bhejti hoon",
                    "card_data": {"action_keyword": "STUDIO", "stamp": "LINK LIVE"},
                    "highlight_word": "comment",
                    "narration_script": "Agar iska direct github link aur setup guide chahiye to comment mein likho studio main seedha tumhare DM mein bhej dungi.",
                    "progress_percent": 100
                }
            ]
        }
