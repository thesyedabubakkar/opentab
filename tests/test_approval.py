import pytest
from core.memory import MemoryManager
from core.approval_gate import ApprovalGate

@pytest.mark.asyncio
async def test_approval_gate():
    mem = MemoryManager()
    await mem.init_db()
    gate = ApprovalGate(mem)

    # Non-sensitive tool
    assert not gate.is_sensitive("search_web", {"query": "weather"})

    # Sensitive tool
    assert gate.is_sensitive("book_reservation", {"restaurant": "Alba", "seats": 2})

    # Sensitive arguments
    assert gate.is_sensitive("custom_action", {"action": "proceed to checkout and pay"})

    # Create approval request
    req = await gate.request_approval("test_session", "book_reservation", {"restaurant": "Alba"})
    assert req["status"] == "requires_approval"
    approval_id = req["approval_id"]

    # Verify retrieval
    retrieved = await mem.get_approval(approval_id)
    assert retrieved is not None
    assert retrieved["status"] == "pending"

    # Resolve approval
    await mem.resolve_approval(approval_id, approved=True)
    resolved = await mem.get_approval(approval_id)
    assert resolved["status"] == "approved"
