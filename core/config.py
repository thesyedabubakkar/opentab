import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    AGENT_NAME: str = "OpenTab"
    DEBUG: bool = True
    PORT: int = int(os.environ.get("PORT", 8000))

    # LLM Settings
    LLM_PROVIDER: str = "ollama"  # 'ollama', 'groq', or 'gemini'
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_MODEL: str = "qwen2.5:7b"

    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "qwen/qwen3.8-27b"

    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # Messaging Channels
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    ENABLE_TELEGRAM: bool = True

    ENABLE_WHATSAPP: bool = False
    WHATSAPP_PORT: int = 3001
    WHATSAPP_WEBHOOK_URL: str = "http://localhost:8000/webhook/whatsapp"

    # Browser (Playwright)
    BROWSER_HEADLESS: bool = True
    BROWSER_TIMEOUT_MS: int = 30000

    # Integrations
    COMPOSIO_API_KEY: Optional[str] = None
    HIGGSFIELD_API_KEY: Optional[str] = None

    # Safety
    REQUIRE_APPROVAL_FOR_SENSITIVE: bool = True

settings = Settings()
