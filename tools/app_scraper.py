import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
from core.config import DATA_DIR, settings

logger = logging.getLogger(__name__)

CAPTURES_DIR = DATA_DIR / "app_captures"
CAPTURES_DIR.mkdir(parents=True, exist_ok=True)

async def capture_app_screens(url: str, domain_tag: Optional[str] = None) -> Dict[str, str]:
    """
    Autonomously navigates to a web application or landing page in mobile viewport (390x844)
    and captures high-resolution screenshots for 3D phone chassis embedding:
    - welcome.png: Top hero / landing screen
    - features.png: Core features section (scrolled)
    - detail.png: Secondary detail / interface section
    """
    from playwright.async_api import async_playwright

    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    # Generate safe folder name
    clean_domain = domain_tag or url.split("//")[-1].split("/")[0].replace(":", "_").replace(".", "_")
    target_dir = CAPTURES_DIR / clean_domain
    target_dir.mkdir(parents=True, exist_ok=True)

    welcome_path = target_dir / "welcome.png"
    features_path = target_dir / "features.png"
    detail_path = target_dir / "detail.png"

    # If already cached and fresh, reuse
    if welcome_path.exists() and features_path.exists() and detail_path.exists():
        logger.info(f"Reusing cached screenshots for {url} in {target_dir}")
        return {
            "welcome": str(welcome_path),
            "features": str(features_path),
            "detail": str(detail_path),
            "domain": clean_domain
        }

    logger.info(f"Scraping live mobile screenshots for {url} (viewport: 390x844)...")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=settings.BROWSER_HEADLESS,
                args=[
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--no-first-run",
                    "--no-zygote",
                    "--renderer-process-limit=1",
                    "--disable-extensions",
                    "--disable-background-networking"
                ]
            )
            # Mobile device emulation (iPhone 14 / modern smartphone viewport)
            context = await browser.new_context(
                viewport={"width": 390, "height": 844},
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
                device_scale_factor=2
            )
            page = await context.new_page()

            # Navigate with 15s timeout
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(1000)
            except Exception as e:
                logger.warning(f"Initial navigation warning for {url}: {e}")

            # Capture 1: Welcome / Hero
            await page.screenshot(path=str(welcome_path), full_page=False)

            # Capture 2: Scroll down 600px for features
            try:
                await page.evaluate("window.scrollBy(0, 650);")
                await page.wait_for_timeout(600)
                await page.screenshot(path=str(features_path), full_page=False)
            except Exception:
                await page.screenshot(path=str(features_path), full_page=False)

            # Capture 3: Scroll further down for feed / detail
            try:
                await page.evaluate("window.scrollBy(0, 900);")
                await page.wait_for_timeout(600)
                await page.screenshot(path=str(detail_path), full_page=False)
            except Exception:
                await page.screenshot(path=str(detail_path), full_page=False)

            await browser.close()

        logger.info(f"Successfully captured mobile screens for {url} in {target_dir}")
        return {
            "welcome": str(welcome_path),
            "features": str(features_path),
            "detail": str(detail_path),
            "domain": clean_domain
        }

    except Exception as e:
        logger.error(f"Failed to scrape live screens for {url}: {e}", exc_info=True)
        # Create fallback high-contrast vector cards if live scraping fails
        _generate_fallback_screens(target_dir, clean_domain)
        return {
            "welcome": str(welcome_path),
            "features": str(features_path),
            "detail": str(detail_path),
            "domain": clean_domain
        }

def _generate_fallback_screens(target_dir: Path, name: str):
    """Generates crisp SVG/PNG fallback mockups when network is offline."""
    from PIL import Image, ImageDraw, ImageFont

    for tag, color in [("welcome", (15, 23, 42)), ("features", (30, 41, 59)), ("detail", (15, 23, 42))]:
        img = Image.new("RGB", (780, 1688), color=color)
        draw = ImageDraw.Draw(img)
        # Draw header & card shapes
        draw.rectangle([60, 120, 720, 200], fill=(59, 130, 246))
        draw.text((100, 145), f"{name.upper()} {tag.upper()}", fill=(255, 255, 255))
        draw.rounded_rectangle([60, 260, 720, 600], radius=24, fill=(51, 65, 85))
        draw.rounded_rectangle([60, 660, 720, 1000], radius=24, fill=(51, 65, 85))
        draw.rounded_rectangle([60, 1060, 720, 1400], radius=24, fill=(51, 65, 85))
        img.save(str(target_dir / f"{tag}.png"))
