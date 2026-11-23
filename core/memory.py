import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import aiosqlite
from core.config import DATA_DIR

logger = logging.getLogger(__name__)

DB_PATH = DATA_DIR / "opentab_memory.db"

class MemoryManager:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path

    async def init_db(self):
        """Initializes tables and indexes."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT,
                    tool_calls TEXT,
                    tool_call_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_profile (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS approvals (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    tool_args TEXT NOT NULL,
                    status TEXT DEFAULT 'pending', -- pending, approved, rejected
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    message TEXT NOT NULL,
                    remind_at TEXT NOT NULL,
                    status TEXT DEFAULT 'pending' -- pending, completed
                )
            """)
            await db.commit()

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        tool_call_id: Optional[str] = None
    ):
        """Appends a message to session history."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO messages (session_id, role, content, tool_calls, tool_call_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    role,
                    content or "",
                    json.dumps(tool_calls) if tool_calls else None,
                    tool_call_id
                )
            )
            await db.commit()

    async def get_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves clean conversational dialogue (user and assistant messages) for context without breaking tool order."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT role, content
                FROM messages
                WHERE session_id = ? AND role IN ('user', 'assistant') AND content IS NOT NULL AND content != ''
                ORDER BY id DESC LIMIT ?
                """,
                (session_id, limit)
            )
            rows = await cursor.fetchall()
            history = []
            for r in reversed(rows):
                history.append({"role": r["role"], "content": r["content"]})
            return history

    async def set_profile(self, key: str, value: Any):
        """Sets a persistent user profile preference."""
        async with aiosqlite.connect(self.db_path) as db:
            val_str = json.dumps(value) if not isinstance(value, str) else value
            await db.execute(
                """
                INSERT INTO user_profile (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
                """,
                (key, val_str)
            )
            await db.commit()

    async def get_profile(self, key: str) -> Optional[Any]:
        """Gets a user profile preference."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT value FROM user_profile WHERE key = ?", (key,))
            row = await cursor.fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except Exception:
                    return row[0]
            return None

    async def get_all_profile(self) -> Dict[str, Any]:
        """Returns the entire profile as a dictionary."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT key, value FROM user_profile")
            rows = await cursor.fetchall()
            res = {}
            for k, v in rows:
                try:
                    res[k] = json.loads(v)
                except Exception:
                    res[k] = v
            return res

    async def create_approval(self, approval_id: str, session_id: str, tool_name: str, tool_args: Dict[str, Any]):
        """Records a pending approval request."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO approvals (id, session_id, tool_name, tool_args, status)
                VALUES (?, ?, ?, ?, 'pending')
                """,
                (approval_id, session_id, tool_name, json.dumps(tool_args))
            )
            await db.commit()

    async def get_approval(self, approval_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves approval details."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,))
            row = await cursor.fetchone()
            if row:
                return {
                    "id": row["id"],
                    "session_id": row["session_id"],
                    "tool_name": row["tool_name"],
                    "tool_args": json.loads(row["tool_args"]),
                    "status": row["status"]
                }
            return None

    async def resolve_approval(self, approval_id: str, approved: bool):
        """Updates approval status."""
        async with aiosqlite.connect(self.db_path) as db:
            new_status = "approved" if approved else "rejected"
            await db.execute(
                "UPDATE approvals SET status = ? WHERE id = ?",
                (new_status, approval_id)
            )
            await db.commit()
