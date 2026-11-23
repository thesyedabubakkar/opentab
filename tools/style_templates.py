from typing import Optional, Dict, Any

def render_dynamic_canvas(
    theme: str,
    product_name: str,
    headline: str,
    subtitle: str,
    tagline: str,
    stamp_text: str,
    highlight_pill: str,
    features: list,
    script_text: str,
    background_image_url: Optional[str] = None,
    screenshot_b64: Optional[str] = None,
    accent_color: str = "#6366f1"
) -> str:
    """Generates a dynamic 9:16 vertical motion canvas matching any requested style theme."""

    # 1. Prepare highlighted subtitles
    words = script_text.split()
    if len(words) >= 4:
        mid = len(words) // 2
        sub_html = f"{' '.join(words[:mid-1])} <span class='sub-highlight'>{' '.join(words[mid-1:mid+2])}</span> {' '.join(words[mid+2:])}"
    else:
        sub_html = f"<span class='sub-highlight'>{script_text}</span>"

    # 2. Features cards HTML
    feature_cards_html = ""
    for f in (features or [])[:3]:
        title = f.get("title", "") if isinstance(f, dict) else str(f)
        desc = f.get("desc", "") if isinstance(f, dict) else ""
        icon = f.get("icon", "✨") if isinstance(f, dict) else "✨"
        feature_cards_html += f"""
        <div class="glass-card">
          <div class="card-icon">{icon}</div>
          <div class="card-content">
            <div class="card-title">{title}</div>
            {f'<div class="card-desc">{desc}</div>' if desc else ''}
          </div>
        </div>
        """

    # 3. Device Mockup or Visual Hero
    if screenshot_b64:
        hero_html = f"""
        <div class="phone-frame">
          <div class="notch"></div>
          <img class="screen-img" src="data:image/jpeg;base64,{screenshot_b64}" alt="Screen" />
        </div>
        """
    elif background_image_url:
        hero_html = f"""
        <div class="art-frame">
          <img class="art-img" src="{background_image_url}" alt="Hero Art" />
        </div>
        """
    else:
        hero_html = f"""
        <div class="phone-frame">
          <div class="notch"></div>
          <div class="screen-content">
            <div class="screen-brand">{product_name}</div>
            <div class="screen-badge">NEW RELEASE</div>
            {feature_cards_html}
          </div>
        </div>
        """

    # THEME A: DARK GLASS / CYBERPUNK (Modern tech, glowing gradients, Apple/Vercel sleekness)
    if theme in ["dark_glass", "cyberpunk", "modern_dark"]:
        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 720px; height: 1280px; overflow: hidden;
    background: #090a0f;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: #ffffff;
    display: flex; flex-direction: column; justify-content: space-between;
    padding: 60px 48px;
    position: relative;
  }}
  .glow-1 {{
    position: absolute; top: -120px; right: -100px; width: 500px; height: 500px;
    background: radial-gradient(circle, {accent_color}55 0%, transparent 70%);
    pointer-events: none; filter: blur(40px);
  }}
  .glow-2 {{
    position: absolute; bottom: 100px; left: -100px; width: 450px; height: 450px;
    background: radial-gradient(circle, #3b82f644 0%, transparent 70%);
    pointer-events: none; filter: blur(50px);
  }}
  .header {{ display: flex; justify-content: space-between; align-items: center; z-index: 10; }}
  .brand-badge {{
    background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.15);
    padding: 10px 20px; border-radius: 999px; font-weight: 800; font-size: 20px;
    letter-spacing: 1px; backdrop-filter: blur(20px);
  }}
  .category-pill {{
    background: {accent_color}22; border: 1px solid {accent_color}66; color: {accent_color};
    padding: 8px 18px; border-radius: 999px; font-weight: 700; font-size: 16px;
  }}
  .hero-section {{ z-index: 10; text-align: center; margin: 30px 0; }}
  .main-headline {{
    font-size: 52px; font-weight: 900; line-height: 1.1; margin-bottom: 16px;
    background: linear-gradient(135deg, #ffffff 40%, rgba(255,255,255,0.6) 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }}
  .sub-tagline {{
    font-size: 22px; color: #94a3b8; font-weight: 600; line-height: 1.4;
  }}
  .center-stage {{
    flex: 1; display: flex; justify-content: center; align-items: center; z-index: 10;
  }}
  .phone-frame {{
    width: 380px; height: 580px; background: #131722; border: 4px solid rgba(255,255,255,0.18);
    border-radius: 40px; box-shadow: 0 30px 60px rgba(0,0,0,0.6), 0 0 40px {accent_color}33;
    overflow: hidden; display: flex; flex-direction: column; position: relative;
  }}
  .notch {{
    width: 140px; height: 24px; background: #000; border-radius: 0 0 16px 16px;
    margin: 0 auto 16px auto;
  }}
  .screen-img {{ width: 100%; height: 100%; object-fit: cover; }}
  .screen-content {{ padding: 24px 20px; flex: 1; display: flex; flex-direction: column; gap: 14px; }}
  .screen-brand {{ font-size: 22px; font-weight: 900; color: #fff; text-align: center; }}
  .screen-badge {{
    background: {accent_color}; color: #fff; font-size: 12px; font-weight: 800;
    padding: 4px 12px; border-radius: 999px; align-self: center; margin-bottom: 8px;
  }}
  .glass-card {{
    background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px; padding: 14px; display: flex; align-items: center; gap: 12px;
  }}
  .card-icon {{ font-size: 24px; }}
  .card-title {{ font-weight: 700; font-size: 16px; color: #fff; }}
  .card-desc {{ font-size: 13px; color: #94a3b8; margin-top: 2px; }}
  .art-frame {{
    width: 500px; height: 500px; border-radius: 32px; overflow: hidden;
    box-shadow: 0 30px 60px rgba(0,0,0,0.7); border: 2px solid rgba(255,255,255,0.2);
  }}
  .art-img {{ width: 100%; height: 100%; object-fit: cover; }}
  .stamp-badge {{
    position: absolute; right: 40px; top: 400px;
    background: {accent_color}; color: #fff; font-weight: 900; font-size: 20px;
    padding: 10px 24px; border-radius: 12px; transform: rotate(-8deg);
    box-shadow: 0 15px 30px rgba(0,0,0,0.4); z-index: 20; letter-spacing: 1px;
  }}
  .footer-subtitles {{
    z-index: 10; background: rgba(0, 0, 0, 0.6); backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 24px;
    padding: 20px 28px; text-align: center;
  }}
  .subtitle-text {{
    font-size: 22px; font-weight: 700; color: #e2e8f0; line-height: 1.4;
  }}
  .sub-highlight {{
    background: #facc15; color: #000; padding: 2px 8px; border-radius: 8px; font-weight: 800;
  }}
</style>
</head>
<body>
  <div class="glow-1"></div>
  <div class="glow-2"></div>
  <div class="header">
    <div class="brand-badge">{product_name}</div>
    <div class="category-pill">{highlight_pill or 'FEATURED'}</div>
  </div>
  <div class="hero-section">
    <div class="main-headline">{headline}</div>
    <div class="sub-tagline">{subtitle or tagline}</div>
  </div>
  <div class="center-stage">
    {hero_html}
    {f'<div class="stamp-badge">{stamp_text}</div>' if stamp_text else ''}
  </div>
  <div class="footer-subtitles">
    <div class="subtitle-text">{sub_html}</div>
  </div>
</body>
</html>"""

    # THEME B: CINEMATIC ART / STORYTELLING (Rich AI art background, filmic letterbox, dramatic aesthetic)
    elif theme in ["cinematic", "film", "story"]:
        bg_style = f"background-image: url('{background_image_url}'); background-size: cover; background-position: center;" if background_image_url else f"background: radial-gradient(circle at center, #1e1b4b 0%, #030712 100%);"
        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 720px; height: 1280px; overflow: hidden;
    {bg_style}
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: #ffffff;
    display: flex; flex-direction: column; justify-content: space-between;
    padding: 80px 48px;
    position: relative;
  }}
  .overlay-shade {{
    position: absolute; inset: 0;
    background: linear-gradient(180deg, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0.2) 50%, rgba(0,0,0,0.85) 100%);
    pointer-events: none;
  }}
  .top-series {{
    z-index: 10; font-size: 18px; font-weight: 800; letter-spacing: 4px;
    text-transform: uppercase; color: {accent_color};
  }}
  .center-story {{
    z-index: 10; display: flex; flex-direction: column; gap: 20px;
  }}
  .story-title {{
    font-size: 56px; font-weight: 900; line-height: 1.1; letter-spacing: -1px;
    text-shadow: 0 10px 30px rgba(0,0,0,0.8);
  }}
  .story-tagline {{
    font-size: 26px; color: #cbd5e1; font-weight: 600; line-height: 1.4;
  }}
  .cinematic-pill {{
    background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(20px);
    padding: 10px 24px; border-radius: 999px; font-size: 18px; font-weight: 700;
    display: inline-block; width: fit-content; border: 1px solid rgba(255,255,255,0.3);
  }}
  .bottom-sub {{
    z-index: 10; background: rgba(0,0,0,0.8); backdrop-filter: blur(25px);
    padding: 24px 32px; border-radius: 24px; border: 1px solid rgba(255,255,255,0.15);
    font-size: 24px; font-weight: 700; line-height: 1.4; text-align: center;
  }}
  .sub-highlight {{
    background: {accent_color}; color: #ffffff; padding: 2px 10px; border-radius: 8px;
  }}
</style>
</head>
<body>
  <div class="overlay-shade"></div>
  <div class="top-series">{product_name} • EXCLUSIVE</div>
  <div class="center-story">
    <div class="cinematic-pill">{highlight_pill or 'DOCUMENTARY'}</div>
    <div class="story-title">{headline}</div>
    <div class="story-tagline">{subtitle or tagline}</div>
  </div>
  <div class="bottom-sub">{sub_html}</div>
</body>
</html>"""

    # THEME C: VIBRANT POP / HIGH-ENERGY VIRAL (Bold energetic gradients, vibrant yellow/pink, high contrast)
    elif theme in ["vibrant_pop", "bold_viral", "energy"]:
        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 720px; height: 1280px; overflow: hidden;
    background: #7c3aed;
    background-image: radial-gradient(at 0% 0%, #ec4899 0px, transparent 50%), radial-gradient(at 100% 100%, #3b82f6 0px, transparent 50%);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: #ffffff;
    display: flex; flex-direction: column; justify-content: space-between;
    padding: 60px 48px;
    position: relative;
  }}
  .badge-tag {{
    background: #facc15; color: #000; font-weight: 900; font-size: 22px;
    padding: 12px 24px; border-radius: 16px; transform: rotate(-3deg);
    display: inline-block; width: fit-content; box-shadow: 0 10px 20px rgba(0,0,0,0.3);
  }}
  .headline-huge {{
    font-size: 58px; font-weight: 900; line-height: 1.05; letter-spacing: -1px;
    margin: 24px 0; text-shadow: 0 8px 24px rgba(0,0,0,0.4);
  }}
  .stage-box {{
    flex: 1; display: flex; justify-content: center; align-items: center;
  }}
  .center-card {{
    background: #ffffff; color: #0f172a; border-radius: 32px; padding: 36px 32px;
    width: 100%; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
    display: flex; flex-direction: column; gap: 16px;
  }}
  .card-top-tag {{ font-size: 16px; font-weight: 900; color: #ec4899; text-transform: uppercase; }}
  .card-main-txt {{ font-size: 32px; font-weight: 900; line-height: 1.2; }}
  .card-sub-txt {{ font-size: 20px; color: #64748b; font-weight: 600; }}
  .viral-sub {{
    background: #111827; border: 3px solid #facc15; border-radius: 24px;
    padding: 22px 30px; text-align: center; font-size: 24px; font-weight: 800; line-height: 1.35;
  }}
  .sub-highlight {{ background: #ec4899; color: #fff; padding: 2px 10px; border-radius: 8px; }}
</style>
</head>
<body>
  <div class="badge-tag">🔥 {product_name.upper()}</div>
  <div class="headline-huge">{headline}</div>
  <div class="stage-box">
    <div class="center-card">
      <div class="card-top-tag">{highlight_pill or 'INSIDER SCOOP'}</div>
      <div class="card-main-txt">{subtitle or headline}</div>
      <div class="card-sub-txt">{tagline}</div>
      {f'<div style="background:#f1f5f9; padding:12px; border-radius:12px; font-weight:800; font-size:18px; text-align:center;">🏷️ {stamp_text}</div>' if stamp_text else ''}
    </div>
  </div>
  <div class="viral-sub">{sub_html}</div>
</body>
</html>"""

    # DEFAULT FALLBACK: NOTEBOOK BUILD-IN-PUBLIC (The classic startup log)
    else:
        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 720px; height: 1280px; overflow: hidden; background: #fdfcf7;
    background-image: linear-gradient(to right, rgba(0,0,0,0.06) 1px, transparent 1px), linear-gradient(to bottom, rgba(0,0,0,0.06) 1px, transparent 1px);
    background-size: 24px 24px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    padding: 60px 48px; display: flex; flex-direction: column; justify-content: space-between;
  }}
  .header-log {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ef4444; padding-bottom: 16px; }}
  .log-title {{ font-weight: 900; font-size: 24px; color: #0f172a; }}
  .log-tag {{ background: #0f172a; color: #facc15; font-weight: 800; padding: 6px 14px; border-radius: 8px; font-size: 15px; }}
  .content-mid {{ display: flex; flex-direction: column; gap: 24px; }}
  .hero-txt {{ font-size: 48px; font-weight: 900; color: #0f172a; line-height: 1.1; }}
  .comp-card {{ background: #fff; border: 2px solid #e2e8f0; border-radius: 20px; padding: 24px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }}
  .stamp-red {{ color: #dc2626; border: 3px solid #dc2626; font-size: 28px; font-weight: 900; padding: 8px 20px; border-radius: 12px; width: fit-content; transform: rotate(-5deg); margin: 10px 0; }}
  .sub-note {{ background: #0f172a; color: #fff; padding: 20px 24px; border-radius: 18px; text-align: center; font-size: 22px; font-weight: 700; line-height: 1.4; }}
  .sub-highlight {{ background: #facc15; color: #000; padding: 2px 8px; border-radius: 6px; font-weight: 900; }}
</style>
</head>
<body>
  <div class="header-log">
    <div class="log-title">{product_name}</div>
    <div class="log-tag">BUILD IN PUBLIC</div>
  </div>
  <div class="content-mid">
    <div class="hero-txt">{headline}</div>
    <div class="comp-card">
      <div style="font-size:22px; font-weight:700; color:#334155; margin-bottom:12px;">{subtitle or tagline}</div>
      {f'<div class="stamp-red">{stamp_text}</div>' if stamp_text else ''}
    </div>
  </div>
  <div class="sub-note">{sub_html}</div>
</body>
</html>"""
