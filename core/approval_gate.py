import uuid
from typing import Any, Dict, Optional, Tuple
from core.config import settings
from core.memory import MemoryManager

# Set of tools or action keywords that require explicit human approval
SENSITIVE_ACTIONS = {
    "submit_form",
    "fill_payment",
    "send_email",
    "delete_file",
    "make_purchase",
    "book_reservation",
    "run_system_command"
}

class ApprovalGate:
    def __init__(self, memory: MemoryManager):
        self.memory = memory

    def is_sensitive(self, tool_name: str, tool_args: Dict[str, Any]) -> bool:
        """Determines if a tool call requires human-in-the-loop approval."""
        if not settings.REQUIRE_APPROVAL_FOR_SENSITIVE:
            return False

        if tool_name in SENSITIVE_ACTIONS:
            return True

        # Check argument intent (e.g., destructive code execution or checkout keywords)
        args_str = str(tool_args).lower()
        triggers = ["checkout", "payment", "book now", "delete", "rmdir", "drop table", "submit order"]
        if any(t in args_str for t in triggers):
            return True

        return False

    async def request_approval(
        self,
        session_id: str,
        tool_name: str,
        tool_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Creates and stores a pending approval request."""
        approval_id = f"appr_{uuid.uuid4().hex[:8]}"
        await self.memory.create_approval(approval_id, session_id, tool_name, tool_args)

        # Human-readable summary
        summary = f"⚠️ **Approval Required**\n\nAction: `{tool_name}`\nDetails: {tool_args}\n\nDo you want to proceed?"
        return {
            "status": "requires_approval",
            "approval_id": approval_id,
            "tool_name": tool_name,
            "tool_args": tool_args,
            "summary": summary
        }
