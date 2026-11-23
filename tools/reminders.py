from datetime import datetime
from typing import Any, Dict
from core.memory import MemoryManager

async def set_user_preference(key: str, value: str) -> Dict[str, Any]:
    """Saves user personal info or preferences into persistent long-term memory."""
    mem = MemoryManager()
    await mem.set_profile(key, value)
    return {"status": "success", "message": f"Saved preference '{key}': {value}"}

PREFERENCE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "set_user_preference",
        "description": "Saves personal facts, dietary restrictions, favorite airlines, or preferences to long-term memory.",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Preference category (e.g. 'dietary_restrictions', 'home_city', 'flight_seat')"},
                "value": {"type": "string", "description": "The preference value (e.g. 'Vegetarian, allergic to peanuts', 'New York')"}
            },
            "required": ["key", "value"]
        }
    }
}
