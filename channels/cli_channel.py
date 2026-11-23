import asyncio
import logging
from core.agent_loop import AgentEngine
from channels.base import BaseChannel

logger = logging.getLogger(__name__)

class CLIChannel(BaseChannel):
    def __init__(self, engine: AgentEngine):
        self.engine = engine
        self.running = False

    async def start(self):
        self.running = True
        session_id = "cli_user"
        print("\n=======================================================")
        print("  OpenTab Agent - Interactive CLI Mode")
        print("  Type your request or 'exit' / 'quit' to stop.")
        print("=======================================================\n")

        loop = asyncio.get_running_loop()
        while self.running:
            try:
                user_input = await loop.run_in_executor(None, input, "You > ")
                if not user_input.strip():
                    continue
                if user_input.strip().lower() in ["exit", "quit"]:
                    print("Exiting OpenTab CLI. Goodbye!")
                    break

                print("\n[*] OpenTab is thinking & executing tools...")
                result = await self.engine.handle_message(session_id=session_id, user_text=user_input)

                if result.get("status") == "requires_approval":
                    print(f"\n{result.get('summary')}")
                    choice = await loop.run_in_executor(None, input, "Approve? [y/n] > ")
                    approved = choice.strip().lower().startswith("y")
                    res = await self.engine.resume_approval(result["approval_id"], approved=approved)
                    print(f"\nOpenTab > {res.get('content')}\n")
                else:
                    print(f"\nOpenTab > {result.get('content')}")
                    if result.get("screenshots"):
                        print(f"[*] Screenshot saved at: {result['screenshots']}")
                    print()

            except (EOFError, KeyboardInterrupt):
                break
            except Exception as e:
                print(f"[!] Error: {e}")

    async def stop(self):
        self.running = False

    async def send_message(self, session_id: str, text: str, **kwargs):
        print(f"\nOpenTab > {text}")
