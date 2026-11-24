import base64
import html
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

def render_scene_html(
    scene: Dict[str, Any],
    topic: str = "Open Higgsfield AI",
    brand_logo_text: str = "शोर",
    brand_sub_text: str = "Crafting Excellence",
    preview_image_path: Optional[str] = None
) -> str:
    """
    Renders high-definition (720x1280) HTML/CSS for a single video scene
    matching Reference Video 1 (SHOR style) and Video 2 (Workflow style).
    """
    category_tag = html.escape(scene.get("category_tag", "TECH SPOTLIGHT"))
    part_label = html.escape(scene.get("part_label", "PART 01"))
    watermark_num = html.escape(str(scene.get("watermark_number", "01")))
    card_type = scene.get("card_type", "window_preview")
    headline = html.escape(scene.get("headline", topic.upper()))
    subtext = html.escape(scene.get("subtext", ""))
    card_data = scene.get("card_data", {})
    progress = max(5, min(100, int(scene.get("progress_percent", 10))))

    # Base64 image embed if preview image exists
    preview_img_tag = ""
    if preview_image_path and Path(preview_image_path).exists():
        try:
            with open(preview_image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                preview_img_tag = f'<img src="data:image/jpeg;base64,{b64}" style="width:100%;height:100%;object-fit:cover;">'
        except Exception as e:
            logger.warning(f"Failed to embed preview image: {e}")

    # Generate Component Content HTML
    component_html = _build_component_html(card_type, card_data, headline, subtext, preview_img_tag)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 720px; height: 1280px; overflow: hidden;
    background-color: #f8f9fa;
    background-image: 
      linear-gradient(to right, rgba(0,0,0,0.04) 1px, transparent 1px),
      linear-gradient(to bottom, rgba(0,0,0,0.04) 1px, transparent 1px);
    background-size: 24px 24px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    color: #0f172a;
    display: flex; flex-direction: column; justify-content: space-between;
    padding: 44px 38px 36px 38px;
    position: relative;
  }}

  /* Top Header */
  .top-header {{
    display: flex; flex-direction: column; align-items: center; gap: 8px; z-index: 10;
  }}
  .brand-logo {{
    font-size: 42px; font-weight: 900; letter-spacing: -1px; color: #000; line-height: 1;
    display: flex; flex-direction: column; align-items: center;
  }}
  .brand-sub {{
    font-size: 11px; font-weight: 800; letter-spacing: 2.5px; text-transform: uppercase; color: #64748b; margin-top: 3px;
  }}
  .top-divider {{
    width: 100%; height: 2px; background: #000; margin-top: 8px; position: relative;
  }}
  .top-divider::before {{
    content: ''; position: absolute; left: 0; top: -2px; width: 40px; height: 6px; background: #000; border-radius: 3px;
  }}
  .sub-header-row {{
    width: 100%; display: flex; justify-content: space-between; align-items: center; margin-top: 10px;
  }}
  .category-badge {{
    font-size: 14px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase; color: #000;
  }}
  .part-counter {{
    font-size: 14px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase; color: #000;
  }}

  /* Giant Embossed Watermark Number */
  .watermark-bg {{
    position: absolute; bottom: 80px; left: 50%; transform: translateX(-50%);
    font-size: 380px; font-weight: 900; line-height: 1;
    color: transparent;
    -webkit-text-stroke: 3px rgba(0, 0, 0, 0.05);
    z-index: 1; pointer-events: none; user-select: none;
  }}

  /* Center Stage */
  .stage-center {{
    flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: center;
    position: relative; z-index: 10; padding: 20px 0;
  }}

  /* Headlines */
  .main-headline {{
    font-size: 44px; font-weight: 900; text-align: center; text-transform: uppercase;
    color: #000; letter-spacing: -0.5px; line-height: 1.15; margin-bottom: 8px;
  }}
  .main-headline span.red {{
    color: #e11d48;
  }}
  .sub-context {{
    font-size: 20px; font-weight: 700; color: #64748b; text-align: center; margin-bottom: 24px;
  }}

  /* Mac Studio Window Component */
  .mac-window {{
    width: 100%; max-width: 620px; background: #111827; border-radius: 18px;
    box-shadow: 0 20px 40px rgba(0,0,0,0.18); overflow: hidden;
    border: 1px solid #1f2937; display: flex; flex-direction: column;
  }}
  .mac-titlebar {{
    background: #0f172a; padding: 12px 16px; display: flex; align-items: center; justify-content: space-between;
    border-bottom: 1px solid #1e293b;
  }}
  .mac-dots {{ display: flex; gap: 7px; }}
  .mac-dot {{ width: 11px; height: 11px; border-radius: 50%; }}
  .dot-red {{ background: #ef4444; }}
  .dot-yellow {{ background: #f59e0b; }}
  .dot-green {{ background: #10b981; }}
  .mac-title {{ font-size: 13px; font-weight: 800; color: #e2e8f0; letter-spacing: 0.5px; }}
  .mac-rec {{ color: #ef4444; margin-left: 6px; }}
  .mac-viewport {{
    width: 100%; height: 260px; background: #030712; position: relative; overflow: hidden;
    display: flex; align-items: center; justify-content: center;
  }}
  .shot-grid {{
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px; width: 100%; height: 100%; padding: 4px;
  }}
  .shot-cell {{
    background: #1f2937; border-radius: 6px; overflow: hidden; position: relative;
    background-size: cover; background-position: center;
  }}
  .mac-scrubber-wrap {{
    background: #0f172a; padding: 10px 16px; display: flex; align-items: center; justify-content: space-between;
  }}
  .mac-playhead {{
    flex: 1; height: 6px; background: #334155; border-radius: 3px; position: relative; margin-right: 14px;
  }}
  .mac-playhead-fill {{
    height: 100%; width: 45%; background: #e11d48; border-radius: 3px;
  }}
  .mac-timecode {{ font-size: 13px; font-weight: 800; color: #94a3b8; font-family: monospace; }}

  /* Comparison Matrix Component */
  .comparison-wrap {{
    width: 100%; display: flex; flex-direction: column; align-items: center; gap: 18px;
  }}
  .tool-pill-header {{
    background: #000; color: #fff; padding: 8px 24px; border-radius: 12px;
    font-size: 24px; font-weight: 900; letter-spacing: 1px; display: flex; align-items: center; gap: 10px;
  }}
  .pill-red-tag {{ background: #e11d48; padding: 2px 10px; border-radius: 6px; font-size: 14px; }}
  .cards-row {{
    display: flex; align-items: center; justify-content: center; gap: 16px; width: 100%;
  }}
  .side-card {{
    flex: 1; background: #fff; border-radius: 18px; padding: 24px 18px; text-align: center;
    box-shadow: 0 10px 25px rgba(0,0,0,0.06); border: 2px solid transparent;
  }}
  .card-left {{ background: #f1f5f9; color: #64748b; }}
  .card-right {{ border-color: #e11d48; position: relative; }}
  .vs-badge {{
    width: 38px; height: 38px; border-radius: 50%; background: #000; color: #fff;
    font-weight: 900; font-size: 15px; display: flex; align-items: center; justify-content: center;
  }}
  .rubber-stamp {{
    border: 3px solid #e11d48; color: #e11d48; font-size: 22px; font-weight: 900;
    padding: 6px 18px; border-radius: 8px; letter-spacing: 1.5px; text-transform: uppercase;
    transform: rotate(-6deg); display: inline-block; margin-top: 14px;
    background: rgba(254, 242, 242, 0.95);
  }}

  /* Step Guide Component */
  .step-card-box {{
    width: 100%; max-width: 580px; background: #fff; border-radius: 20px;
    padding: 24px; box-shadow: 0 12px 30px rgba(0,0,0,0.07); border: 2px solid #e2e8f0;
  }}
  .step-header-row {{ display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }}
  .step-pill {{
    background: #e11d48; color: #fff; font-size: 15px; font-weight: 900; padding: 5px 14px; border-radius: 7px;
  }}
  .step-title {{ font-size: 24px; font-weight: 900; color: #000; }}
  .step-input-row {{
    display: flex; align-items: center; gap: 12px; background: #f8fafc; border: 1.5px solid #cbd5e1;
    border-radius: 12px; padding: 12px 16px;
  }}
  .step-url {{ flex: 1; font-size: 16px; font-weight: 700; color: #334155; font-family: monospace; }}
  .step-progress-badge {{
    background: #e11d48; color: #fff; font-size: 16px; font-weight: 900; padding: 6px 18px; border-radius: 8px;
  }}

  /* Waveform & Terminal Component */
  .waveform-box {{
    width: 100%; max-width: 580px; background: #fef3c7; border: 3px solid #b45309;
    border-radius: 20px; padding: 24px; box-shadow: 0 12px 25px rgba(180, 83, 9, 0.12);
    display: flex; flex-direction: column; gap: 14px;
  }}
  .waveform-title {{ font-size: 36px; font-weight: 900; color: #78350f; }}
  .waveform-sub {{ font-size: 16px; font-weight: 700; color: #92400e; }}
  .wave-bars {{
    display: flex; align-items: center; justify-content: space-between; height: 48px; gap: 4px;
  }}
  .wave-bar {{
    flex: 1; background: #b45309; border-radius: 3px;
  }}
  .terminal-pill {{
    background: #111827; color: #34d399; font-family: monospace; font-size: 14px; font-weight: 800;
    padding: 10px 16px; border-radius: 10px; display: flex; align-items: center; gap: 8px;
    border: 1px solid #1f2937;
  }}

  /* Bar Chart Component */
  .barchart-box {{
    width: 100%; max-width: 580px; background: #fef3c7; border: 3px solid #b45309;
    border-radius: 20px; padding: 24px; box-shadow: 0 12px 25px rgba(180, 83, 9, 0.12);
  }}
  .pro-tip-tag {{
    background: #991b1b; color: #fff; font-size: 14px; font-weight: 900; padding: 4px 14px;
    border-radius: 12px; display: inline-block; margin-bottom: 12px;
  }}
  .chart-flex {{
    display: flex; align-items: flex-end; justify-content: center; gap: 40px; height: 180px; margin-top: 16px;
  }}
  .chart-col {{
    display: flex; flex-direction: column; align-items: center; gap: 8px; width: 140px;
  }}
  .chart-bar-1 {{
    width: 100%; height: 25px; background: #78350f; border-radius: 6px;
  }}
  .chart-bar-2 {{
    width: 100%; height: 150px; background: #991b1b; border-radius: 6px;
  }}
  .col-val {{ font-size: 22px; font-weight: 900; color: #000; }}
  .col-lbl {{ font-size: 15px; font-weight: 800; color: #78350f; }}

  /* Pricing Breakdown Component */
  .pricing-stack {{
    width: 100%; max-width: 580px; display: flex; flex-direction: column; gap: 14px;
  }}
  .price-row-card {{
    background: #fff; border-radius: 16px; padding: 18px 24px;
    display: flex; justify-content: space-between; align-items: center;
    box-shadow: 0 8px 20px rgba(0,0,0,0.05); border: 1.5px solid #e2e8f0;
  }}
  .price-name {{ font-size: 24px; font-weight: 900; color: #1e293b; }}
  .price-val {{ font-size: 22px; font-weight: 900; color: #e11d48; }}

  /* Bottom Checkpoint Scrub Bar */
  .bottom-scrub-bar {{
    width: 100%; display: flex; flex-direction: column; gap: 6px; z-index: 10;
  }}
  .scrub-track-wrapper {{
    position: relative; width: 100%; height: 26px; display: flex; align-items: center;
  }}
  .scrub-line-bg {{
    width: 100%; height: 3px; background: #cbd5e1; border-radius: 2px; position: absolute; left: 0; right: 0;
  }}
  .scrub-line-fill {{
    height: 3px; background: #e11d48; border-radius: 2px; position: absolute; left: 0; width: {progress}%;
  }}
  .scrub-ball {{
    width: 18px; height: 18px; border-radius: 50%; background: #000; position: absolute;
    left: calc({progress}% - 9px); top: 4px; box-shadow: 0 2px 6px rgba(0,0,0,0.3);
  }}
  .flag-marker {{
    position: absolute; left: 24%; top: -8px; width: 12px; height: 12px;
  }}
  .checkpoints-row {{
    display: flex; justify-content: space-between; font-size: 12px; font-weight: 900; color: #64748b;
  }}
  .cp-active {{ color: #e11d48; }}
  .scrub-footer-meta {{
    display: flex; justify-content: space-between; font-size: 12px; font-weight: 800; color: #475569;
  }}
</style>
</head>
<body>

  <!-- Top Header Section -->
  <div class="top-header">
    <div class="brand-logo">
      {brand_logo_text}
      <div class="brand-sub">{brand_sub_text}</div>
    </div>
    <div class="top-divider"></div>
    <div class="sub-header-row">
      <div class="category-badge">{category_tag}</div>
      <div class="part-counter">{part_label}</div>
    </div>
  </div>

  <!-- Giant Embossed Background Number -->
  <div class="watermark-bg">{watermark_num}</div>

  <!-- Center Stage Visual Component -->
  <div class="stage-center">
    {component_html}
  </div>

  <!-- Bottom Checkpoint Scrub Bar -->
  <div class="bottom-scrub-bar">
    <div class="scrub-track-wrapper">
      <div class="scrub-line-bg"></div>
      <div class="scrub-line-fill"></div>
      <div class="scrub-ball"></div>
    </div>
    <div class="checkpoints-row">
      <span class="{'cp-active' if progress >= 10 else ''}">P1</span>
      <span class="{'cp-active' if progress >= 25 else ''}">P3</span>
      <span class="{'cp-active' if progress >= 45 else ''}">P5</span>
      <span class="{'cp-active' if progress >= 65 else ''}">P7</span>
      <span class="{'cp-active' if progress >= 85 else ''}">P9</span>
      <span class="{'cp-active' if progress >= 95 else ''}">P11</span>
    </div>
    <div class="scrub-footer-meta">
      <span>{topic} · free</span>
      <span>{part_label}</span>
    </div>
  </div>

</body>
</html>
"""

def _build_component_html(card_type: str, card_data: Dict[str, Any], headline: str, subtext: str, preview_img: str) -> str:
    """Builds specific visual layout cards matching the reference video types."""
    
    if card_type == "comparison_matrix":
        left = card_data.get("left_label", "Original $50/mo")
        right = card_data.get("right_label", "Open Source FREE")
        stamp = card_data.get("stamp", "</> OPEN SOURCE")
        return f"""
        <div class="main-headline">{headline}</div>
        <div class="sub-context">{subtext}</div>
        <div class="comparison-wrap">
          <div class="cards-row">
            <div class="side-card card-left">
              <div style="font-size: 20px; font-weight: 800;">{left}</div>
            </div>
            <div class="vs-badge">VS</div>
            <div class="side-card card-right">
              <div style="font-size: 22px; font-weight: 900; color: #e11d48;">{right}</div>
            </div>
          </div>
          <div class="rubber-stamp">{stamp}</div>
        </div>
        """

    elif card_type == "step_guide":
        step_num = card_data.get("step_num", "STEP 1")
        title = card_data.get("title", "GitHub se download")
        url = card_data.get("url", "github.com / Open Higgsfield AI")
        badge = card_data.get("badge", "15%")
        return f"""
        <div class="main-headline">{headline}</div>
        <div class="sub-context">{subtext}</div>
        <div class="step-card-box">
          <div class="step-header-row">
            <div class="step-pill">{step_num}</div>
            <div class="step-title">{title}</div>
          </div>
          <div class="step-input-row">
            <div class="step-url">{url}</div>
            <div class="step-progress-badge">{badge}</div>
          </div>
        </div>
        """

    elif card_type == "waveform_spec":
        tool_name = card_data.get("tool_name", "Kokoro")
        device = card_data.get("device", "Voice model · runs on your laptop")
        status = card_data.get("status", "Claude: installing Kokoro... 99%")
        return f"""
        <div class="main-headline">{headline}</div>
        <div class="sub-context">{subtext}</div>
        <div class="waveform-box">
          <div>
            <div class="waveform-title">{tool_name}</div>
            <div class="waveform-sub">{device}</div>
          </div>
          <div class="wave-bars">
            <div class="wave-bar" style="height: 35%;"></div>
            <div class="wave-bar" style="height: 70%;"></div>
            <div class="wave-bar" style="height: 100%;"></div>
            <div class="wave-bar" style="height: 40%;"></div>
            <div class="wave-bar" style="height: 85%;"></div>
            <div class="wave-bar" style="height: 60%;"></div>
            <div class="wave-bar" style="height: 95%;"></div>
            <div class="wave-bar" style="height: 50%;"></div>
            <div class="wave-bar" style="height: 80%;"></div>
            <div class="wave-bar" style="height: 30%;"></div>
          </div>
          <div class="terminal-pill">
            <span>✸</span> {status}
          </div>
        </div>
        """

    elif card_type == "barchart_comparison":
        title = card_data.get("title", "Earnings per 1,000 views")
        item1 = card_data.get("item1", "India ≈ ₹65")
        item2 = card_data.get("item2", "USA ≈ ₹924")
        return f"""
        <div class="main-headline">{headline}</div>
        <div class="sub-context">{subtext}</div>
        <div class="barchart-box">
          <div class="pro-tip-tag">★ PRO TIP</div>
          <div style="font-size: 18px; font-weight: 800; color: #78350f;">{title}</div>
          <div class="chart-flex">
            <div class="chart-col">
              <div class="col-val">≈ ₹65</div>
              <div class="chart-bar-1"></div>
              <div class="col-lbl">🇮🇳 India</div>
            </div>
            <div class="chart-col">
              <div class="col-val">≈ ₹924</div>
              <div class="chart-bar-2"></div>
              <div class="col-lbl">🇺🇸 USA</div>
            </div>
          </div>
        </div>
        """

    elif card_type == "pricing_breakdown":
        items = card_data.get("items", [
            {"name": "Image tool", "price": "₹₹₹ / month"},
            {"name": "Video tool", "price": "₹₹₹ / month"},
            {"name": "Voice tool", "price": "₹₹₹ / month"}
        ])
        rows = "".join(f"""
        <div class="price-row-card">
          <div class="price-name">{it['name']}</div>
          <div class="price-val">{it['price']}</div>
        </div>
        """ for it in items)
        return f"""
        <div class="main-headline">{headline}</div>
        <div class="sub-context">{subtext}</div>
        <div class="pricing-stack">
          {rows}
        </div>
        """

    elif card_type == "cta_card":
        action = card_data.get("action_keyword", "STUDIO")
        stamp = card_data.get("stamp", "DM SENT")
        return f"""
        <div class="main-headline">{headline}</div>
        <div class="sub-context">{subtext}</div>
        <div class="comparison-wrap">
          <div class="side-card" style="width: 100%; max-width: 540px; border: 3px solid #000; padding: 32px 20px;">
            <div style="font-size: 26px; font-weight: 900; margin-bottom: 12px;">COMMENT <span style="color:#e11d48;">"{action}"</span></div>
            <div style="font-size: 16px; font-weight: 700; color: #64748b;">Direct link & setup guide seedha DM mein milegi!</div>
          </div>
          <div class="rubber-stamp" style="border-color:#10b981; color:#10b981;">{stamp}</div>
        </div>
        """

    # Default: Mac Studio Window Component
    window_title = card_data.get("window_title", "AI Studio REC")
    timecode = card_data.get("timecode", "00:02:18")
    has_grid = card_data.get("has_grid", True)

    viewport_content = preview_img
    if not viewport_content and has_grid:
        viewport_content = """
        <div class="shot-grid">
          <div class="shot-cell" style="background:#1e293b;"></div>
          <div class="shot-cell" style="background:#334155;"></div>
          <div class="shot-cell" style="background:#475569;"></div>
          <div class="shot-cell" style="background:#64748b;"></div>
          <div class="shot-cell" style="background:#0f172a;"></div>
          <div class="shot-cell" style="background:#1e293b;"></div>
        </div>
        """
    elif not viewport_content:
        viewport_content = '<div style="color:#64748b; font-weight:800; font-size:18px;">4K CINEMA PREVIEW</div>'

    return f"""
    <div class="main-headline">{headline}</div>
    <div class="sub-context">{subtext}</div>
    <div class="mac-window">
      <div class="mac-titlebar">
        <div class="mac-dots">
          <div class="mac-dot dot-red"></div>
          <div class="mac-dot dot-yellow"></div>
          <div class="mac-dot dot-green"></div>
        </div>
        <div class="mac-title">{window_title} <span class="mac-rec">●</span></div>
        <div style="width: 40px;"></div>
      </div>
      <div class="mac-viewport">
        {viewport_content}
      </div>
      <div class="mac-scrubber-wrap">
        <div class="mac-playhead">
          <div class="mac-playhead-fill"></div>
        </div>
        <div class="mac-timecode">{timecode}</div>
      </div>
    </div>
    """
