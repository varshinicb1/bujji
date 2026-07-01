import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from bujji.core.models import MemoryEntry
from bujji.memory.base import MemoryBackend


class SQLiteMemory(MemoryBackend):
    """SQLite-based persistent memory storage."""

    def __init__(self, db_path: str) -> None:
        self.db_path = str(Path(db_path).expanduser().resolve())
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
        return self._conn

    async def _init_db(self) -> None:
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                entry_type TEXT NOT NULL DEFAULT 'general',
                metadata TEXT NOT NULL DEFAULT '{}',
                timestamp TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_type
            ON memories(entry_type)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_timestamp
            ON memories(timestamp)
        """)
        conn.commit()

    async def store(self, entry: MemoryEntry) -> str:
        await self._init_db()
        entry_id = entry.id or str(uuid.uuid4())
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO memories (id, content, entry_type, metadata, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (
                entry_id,
                entry.content,
                entry.entry_type,
                json.dumps(entry.metadata),
                entry.timestamp.isoformat(),
            ),
        )
        conn.commit()
        return entry_id

    async def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        await self._init_db()
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM memories WHERE id = ?", (entry_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return MemoryEntry(
            id=row["id"],
            content=row["content"],
            entry_type=row["entry_type"],
            metadata=json.loads(row["metadata"]),
            timestamp=datetime.fromisoformat(row["timestamp"]),
        )

    async def search(
        self,
        query: str,
        limit: int = 10,
        entry_type: Optional[str] = None,
    ) -> list[MemoryEntry]:
        await self._init_db()
        conn = self._get_conn()
        if entry_type:
            cursor = conn.execute(
                """SELECT * FROM memories
                   WHERE entry_type = ? AND content LIKE ?
                   ORDER BY timestamp DESC LIMIT ?""",
                (entry_type, f"%{query}%", limit),
            )
        else:
            cursor = conn.execute(
                """SELECT * FROM memories
                   WHERE content LIKE ?
                   ORDER BY timestamp DESC LIMIT ?""",
                (f"%{query}%", limit),
            )
        rows = cursor.fetchall()

        return [
            MemoryEntry(
                id=row["id"],
                content=row["content"],
                entry_type=row["entry_type"],
                metadata=json.loads(row["metadata"]),
                timestamp=datetime.fromisoformat(row["timestamp"]),
            )
            for row in rows
        ]

    async def delete(self, entry_id: str) -> bool:
        await self._init_db()
        conn = self._get_conn()
        cursor = conn.execute(
            "DELETE FROM memories WHERE id = ?", (entry_id,)
        )
        conn.commit()
        return cursor.rowcount > 0

    async def list_by_type(
        self,
        entry_type: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MemoryEntry]:
        await self._init_db()
        conn = self._get_conn()
        cursor = conn.execute(
            """SELECT * FROM memories
               WHERE entry_type = ?
               ORDER BY timestamp DESC LIMIT ? OFFSET ?""",
            (entry_type, limit, offset),
        )
        rows = cursor.fetchall()

        return [
            MemoryEntry(
                id=row["id"],
                content=row["content"],
                entry_type=row["entry_type"],
                metadata=json.loads(row["metadata"]),
                timestamp=datetime.fromisoformat(row["timestamp"]),
            )
            for row in rows
        ]

    async def clear(self) -> None:
        await self._init_db()
        conn = self._get_conn()
        conn.execute("DELETE FROM memories")
        conn.commit()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    async def get_stats(self) -> dict[str, Any]:
        await self._init_db()
        conn = self._get_conn()
        total = conn.execute("SELECT COUNT(*) as count FROM memories").fetchone()["count"]
        by_type_rows = conn.execute(
            """SELECT entry_type, COUNT(*) as count
               FROM memories GROUP BY entry_type"""
        ).fetchall()
        by_type = {row["entry_type"]: row["count"] for row in by_type_rows}

        return {
            "backend": "sqlite",
            "total_entries": total,
            "entries_by_type": by_type,
            "db_path": self.db_path,
        }
