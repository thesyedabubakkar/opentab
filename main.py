import argparse
import asyncio
import logging
import signal
import sys
from core.config import settings
from core.agent_loop import AgentEngine
from tools.browser_tool import PlaywrightBrowser
from channels.telegram_channel import TelegramChannel
from channels.whatsapp_bridge import WhatsAppBridge
from channels.cli_channel import CLIChannel

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("OpenTab")

async def main():
    parser = argparse.ArgumentParser(description="OpenTab 100% Open-Source Autonomous Personal Assistant")
    parser.add_argument(
        "--mode",
        choices=["cli", "telegram", "whatsapp", "all"],
        default="cli",
        help="Run mode (default: cli for instant interactive testing; use 'all' or 'telegram'/'whatsapp' for messaging bots)"
    )
    args = parser.parse_args()

    print("=============================================================")
    print("   OpenTab - 100% Open-Source Autonomous Agent Architecture  ")
    print("   Modeled after Tab (tab.bot) | Free & Fully Self-Hosted    ")
    print("=============================================================")
    print(f"[*] Active LLM Provider: {settings.LLM_PROVIDER.upper()}")
    print(f"[*] Playwright Browser: Local Chromium (Headless: {settings.BROWSER_HEADLESS})")

    engine = AgentEngine()
    await engine.initialize()

    active_channels = []

    if args.mode in ["cli"]:
        cli = CLIChannel(engine)
        active_channels.append(cli)
        await cli.start()
    else:
        # Telegram Channel
        if args.mode in ["telegram", "all"] and settings.ENABLE_TELEGRAM:
            if settings.TELEGRAM_BOT_TOKEN:
                tg = TelegramChannel(engine)
                active_channels.append(tg)
                asyncio.create_task(tg.start())
                print("[+] Telegram Gateway initialized.")
            else:
                print("[!] TELEGRAM_BOT_TOKEN not found in .env (add token from @BotFather).")

        # HTTP Health Server & WhatsApp Webhook
        if args.mode in ["whatsapp", "all", "telegram"]:
            wa = WhatsAppBridge(engine)
            active_channels.append(wa)
            asyncio.create_task(wa.start())
            print(f"[+] HTTP Server & Health Check listening on port {settings.PORT}.")

            # 24/7 Keep-Alive self ping (prevents Render Free Tier from sleeping)
            async def _keep_alive():
                import httpx
                await asyncio.sleep(60)
                while True:
                    try:
                        async with httpx.AsyncClient(timeout=30) as client:
                            await client.get("https://opentab-agent.onrender.com/health")
                    except Exception:
                        pass
                    await asyncio.sleep(540) # Every 9 minutes
            asyncio.create_task(_keep_alive())

        print("\n[*] OpenTab daemon is running. Press Ctrl+C to exit.\n")
        # Keep process alive
        stop_event = asyncio.Event()

        def _signal_handler():
            stop_event.set()

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop = asyncio.get_running_loop()
                loop.add_signal_handler(sig, _signal_handler)
            except (NotImplementedError, AttributeError):
                pass  # Windows does not support add_signal_handler

        try:
            while not stop_event.is_set():
                await asyncio.sleep(1)
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass

    # Cleanup
    print("\n[*] Shutting down OpenTab...")
    for ch in active_channels:
        try:
            await ch.stop()
        except Exception:
            pass

    browser = PlaywrightBrowser.get_instance()
    await browser.close()
    print("[+] All services stopped cleanly.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
