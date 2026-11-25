import pytest
from core.agent_loop import AgentEngine

@pytest.mark.asyncio
async def test_unfiltered_action_generates_image_without_questions():
    engine = AgentEngine()
    user_prompt = "Add my character in this by replacing it without effecting anything other please"

    res = await engine.handle_message(
        session_id="test_unfiltered_session",
        user_text=user_prompt
    )

    assert res.get("status") == "complete"
    # Verify image was produced and attached
    images = res.get("images", [])
    assert len(images) > 0, "Engine failed to produce image file!"
    
    # Verify response contains no banned questionnaires
    content = (res.get("content") or "").lower()
    assert "quick questions" not in content, "Response contained a questionnaire!"
    assert "tell me what you're after" not in content, "Response contained stall text!"
    assert "what are your character" not in content, "Response asked for character features!"
