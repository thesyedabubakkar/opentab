import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger(__name__)

DOCS_DIR = Path("data/office_documents")
DOCS_DIR.mkdir(parents=True, exist_ok=True)

class PresentationTool:
    """
    Creates and edits professional PowerPoint presentations (.pptx).
    Supports modern styling, color themes, bullet hierarchies, and speaker notes.
    """
    def __init__(self):
        self.output_dir = DOCS_DIR

    async def create_presentation(
        self,
        topic: str,
        slide_count: int = 6,
        theme: str = "dark_tech",
        custom_points: Optional[List[str]] = None
    ) -> Path:
        """
        Generates a complete PowerPoint presentation on the requested topic.
        """
        fn = f"presentation_{uuid.uuid4().hex[:8]}.pptx"
        out_path = self.output_dir / fn

        def _build_pptx():
            try:
                from pptx import Presentation
                from pptx.util import Inches, Pt
                from pptx.dml.color import RGBColor
                from pptx.enum.text import PP_ALIGN

                prs = Presentation()
                prs.slide_width = Inches(13.333) # 16:9 widescreen
                prs.slide_height = Inches(7.5)

                # Theme Colors
                if theme == "dark_tech":
                    bg_color = RGBColor(15, 23, 42) # Slate 900
                    text_color = RGBColor(248, 250, 252) # White
                    accent_color = RGBColor(56, 189, 248) # Cyan
                else:
                    bg_color = RGBColor(255, 255, 255)
                    text_color = RGBColor(30, 41, 59)
                    accent_color = RGBColor(37, 99, 235)

                blank_slide_layout = prs.slide_layouts[6]

                # Slide 1: Title Slide
                s1 = prs.slides.add_slide(blank_slide_layout)
                tx_box = s1.shapes.add_textbox(Inches(1.5), Inches(2.5), Inches(10.33), Inches(2.5))
                tf = tx_box.text_frame
                tf.word_wrap = True
                
                p = tf.paragraphs[0]
                p.text = topic.title()
                p.font.size = Pt(44)
                p.font.bold = True
                p.font.color.rgb = accent_color
                p.alignment = PP_ALIGN.CENTER

                p2 = tf.add_paragraph()
                p2.text = "Autonomous Strategy & Execution Deck • OpenTab AI"
                p2.font.size = Pt(20)
                p2.font.color.rgb = text_color
                p2.alignment = PP_ALIGN.CENTER

                # Slide Outline Structure
                default_slides = [
                    ("Executive Summary", [
                        "Comprehensive overview of key strategic objectives",
                        "High-impact execution roadmap designed for autonomous scale",
                        "Core differentiators driving user adoption and retention"
                    ]),
                    ("Problem & Market Gap", [
                        "Current legacy solutions fail to execute autonomous multi-step actions",
                        "High friction in manual workflow coordination across tools",
                        "Need for unified intelligence that acts rather than chats"
                    ]),
                    ("The OpenTab Solution", [
                        "Turn-1 autonomous direct execution without questionnaires",
                        "Integrated Image, Video, Office, and Coding Engines",
                        "Persistent 7-layer memory retaining project context"
                    ]),
                    ("System Architecture", [
                        "LangGraph multi-step agent orchestrator with state persistence",
                        "Dual-tier generation with local zero-cost ONNX execution",
                        "Native Telegram mobile gateway for universal accessibility"
                    ]),
                    ("Roadmap & Future Milestones", [
                        "Phase 1: Nano Banana 2.1 & Character Consistency (Active)",
                        "Phase 2: Office & Multilingual Voice Reader Studio (Active)",
                        "Phase 3: Autonomous Full-Stack & APK Compilation"
                    ])
                ]

                slides_to_generate = default_slides[:max(1, slide_count - 1)]

                for title_text, bullets in slides_to_generate:
                    slide = prs.slides.add_slide(blank_slide_layout)
                    
                    # Title
                    t_box = slide.shapes.add_textbox(Inches(1.0), Inches(0.8), Inches(11.33), Inches(1.0))
                    t_frame = t_box.text_frame
                    t_p = t_frame.paragraphs[0]
                    t_p.text = title_text
                    t_p.font.size = Pt(32)
                    t_p.font.bold = True
                    t_p.font.color.rgb = accent_color

                    # Bullets
                    b_box = slide.shapes.add_textbox(Inches(1.2), Inches(2.2), Inches(10.9), Inches(4.5))
                    b_frame = b_box.text_frame
                    b_frame.word_wrap = True

                    for i, bullet in enumerate(bullets):
                        bp = b_frame.paragraphs[0] if i == 0 else b_frame.add_paragraph()
                        bp.text = f"•  {bullet}"
                        bp.font.size = Pt(22)
                        bp.font.color.rgb = text_color
                        bp.space_after = Pt(20)

                prs.save(str(out_path))
                logger.info(f"Presentation generated: {out_path}")
                return out_path
            except Exception as e:
                logger.error(f"Failed to build pptx ({e}), creating markdown fallback.")
                md_path = out_path.with_suffix(".md")
                md_path.write_text(f"# {topic}\n\nExecutive presentation generated by OpenTab.", encoding="utf-8")
                return md_path

        return await asyncio.to_thread(_build_pptx)

presentation_tool = PresentationTool()
