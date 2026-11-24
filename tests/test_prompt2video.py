import pytest
from core.prompt2video_director import Prompt2VideoDirector

@pytest.mark.asyncio
async def test_director_shor_style():
    director = Prompt2VideoDirector()
    sb = await director.direct("Make a viral video explaining Open Higgsfield AI")
    assert "scenes" in sb
    assert len(sb["scenes"]) >= 4
    first_scene = sb["scenes"][0]
    assert "category_tag" in first_scene
    assert "part_label" in first_scene
    assert "progress_percent" in first_scene

@pytest.mark.asyncio
async def test_director_workflow_style():
    director = Prompt2VideoDirector()
    sb = await director.direct("How to automate history videos with Claude Code and Kokoro")
    assert "scenes" in sb
    assert len(sb["scenes"]) >= 4
    has_waveform_or_step = any(s.get("card_type") in ["waveform_spec", "step_guide", "barchart_comparison"] for s in sb["scenes"])
    assert has_waveform_or_step
