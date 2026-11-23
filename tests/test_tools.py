import pytest
from tools.search_tool import search_web
from tools.code_runner import run_python_code
from tools.reminders import set_user_preference
from core.memory import MemoryManager

@pytest.mark.asyncio
async def test_search_web():
    results = await search_web("Python programming language", max_results=2)
    assert isinstance(results, list)
    assert len(results) > 0
    assert "Python" in results[0]["title"] or "Python" in results[0]["snippet"]

@pytest.mark.asyncio
async def test_code_runner():
    code = "result = sum([x**2 for x in range(5)])"
    res = await run_python_code(code)
    assert res["status"] == "success"
    assert res["result"] == 30  # 0+1+4+9+16 = 30

@pytest.mark.asyncio
async def test_memory_and_preferences():
    mem = MemoryManager()
    await mem.init_db()
    await set_user_preference("favorite_cuisine", "Italian")
    val = await mem.get_profile("favorite_cuisine")
    assert val == "Italian"
