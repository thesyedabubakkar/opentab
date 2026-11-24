import pytest
from pathlib import Path
from tools.higgsfield_client import OpenHiggsfieldClient

@pytest.mark.asyncio
async def test_higgsfield_free_fallback():
    client = OpenHiggsfieldClient()
    out = await client.generate_media("futuristic AI cinema studio", media_type="image")
    assert Path(out).exists()
    assert Path(out).stat().st_size > 0
