# OpenTab: 100% Free & Open-Source Autonomous Personal Assistant

Modeled after **[Tab (tab.bot)](https://tab.bot/)**, **OpenTab** is a self-hosted, 100% open-source personal AI assistant you can text over **Telegram** or **WhatsApp**. It executes real-world tasks using autonomous web browsing, tool calling, and human-in-the-loop approval gates.

---

## Key Features

1. **Dual Messaging Channels**:
   - **Telegram Gateway**: 100% free via Telegram Bot API with inline interactive buttons for approvals and screenshot delivery.
   - **WhatsApp Gateway**: 100% free local bridge via Baileys multi-device protocol (pair directly via QR code with your phone).
   - **Interactive CLI**: Instant local terminal chat for testing and development.
2. **Local & Free Cloud LLMs**:
   - **Local Ollama**: 100% private & offline (Llama 3.2, Qwen 2.5, DeepSeek R1).
   - **Free Cloud Providers**: Fast, zero-cost reasoning with Groq (Llama 3.3 70B) or Google Gemini (Flash).
3. **Local Web Navigation (Playwright)**:
   - Headless Chromium with stealth mode.
   - Automatic DOM cleaning & token-efficient Markdown extraction.
   - Visual screenshot proof sent directly to your phone.
4. **Composio & Builtin Tools**:
   - Free web search (DuckDuckGo, zero API keys required).
   - Python code interpreter for calculations and conversions.
   - Long-term persistent memory for personal facts and preferences (SQLite).
   - Composio integration for 200+ connected apps (Gmail, GitHub, Slack, Notion).
5. **Human-in-the-Loop Approval Gates**:
   - Sensitive actions (purchases, destructive modifications, form submissions) pause execution and send an interactive `[Approve] / [Reject]` prompt to your chat before proceeding.

---

## Quick Start

### 1. Launch with One-Click
Double click **`run.bat`** or run:
```cmd
run.bat
```
Choose from the interactive menu:
- `[1]` Interactive CLI Mode
- `[2]` Start Telegram Bot Gateway
- `[3]` Start WhatsApp Bridge (Node.js QR connector + Python agent)
- `[4]` Start All Gateways
- `[5]` Run Automated Test Suite

### 2. Configuration (`.env`)
Edit `.env` to configure your preferred services:
```env
# Choose LLM: 'ollama', 'groq', or 'gemini'
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:7b

# (Optional) Cloud free tier keys:
GROQ_API_KEY=
GEMINI_API_KEY=

# (Optional) Telegram Bot token from @BotFather:
TELEGRAM_BOT_TOKEN=
ENABLE_TELEGRAM=True

# WhatsApp Bridge:
ENABLE_WHATSAPP=True
```

---

## Project Structure
```
yera/
├── .env.example            # Environment configuration template
├── .env                    # Active configuration
├── requirements.txt        # Python dependencies
├── package.json            # Node.js dependencies (Baileys WhatsApp)
├── run.bat                 # Windows one-click launcher
├── main.py                 # Central daemon & CLI entrypoint
├── pytest.ini              # Test runner configuration
├── core/
│   ├── config.py           # Settings manager
│   ├── llm_client.py       # Multi-provider async LLM client
│   ├── agent_loop.py       # ReAct autonomous reasoning engine
│   ├── memory.py           # SQLite persistent memory & approvals
│   └── approval_gate.py    # Sensitive action detection & approval
├── tools/
│   ├── registry.py         # Tool registry & function calling schemas
│   ├── browser_tool.py     # Playwright headless browser & screenshots
│   ├── search_tool.py      # DuckDuckGo 100% free search
│   ├── code_runner.py      # Python code sandbox
│   ├── reminders.py        # User profile & preference memory
│   └── composio_tool.py    # Composio SDK connector
├── channels/
│   ├── base.py             # Channel abstract base class
│   ├── telegram_channel.py # Telegram bot gateway
│   ├── whatsapp_bridge.py  # Python webhook for WhatsApp
│   ├── whatsapp_service.js # Node.js Baileys QR-code connector
│   └── cli_channel.py      # Terminal interactive chat
└── tests/
    ├── test_approval.py    # Approval gate tests
    ├── test_browser.py     # Playwright web navigation tests
    └── test_tools.py       # Search, math, and memory tests
```
