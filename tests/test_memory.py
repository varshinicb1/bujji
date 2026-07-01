import tempfile
from pathlib import Path

import pytest

from bujji.core.models import MemoryEntry
from bujji.memory.manager import MemoryManager
from bujji.memory.sqlite_backend import SQLiteMemory


@pytest.fixture
def sqlite_memory():
    db_path = tempfile.mktemp(suffix=".db")
    mem = SQLiteMemory(db_path)
    yield mem
    mem.close()
    import time
    time.sleep(0.05)
    try:
        Path(db_path).unlink(missing_ok=True)
    except PermissionError:
        pass


@pytest.mark.asyncio
class TestSQLiteMemory:
    async def test_store_and_retrieve(self, sqlite_memory):
        entry_id = await sqlite_memory.store(
            MemoryEntry(content="test entry", entry_type="test")
        )
        assert entry_id is not None

        retrieved = await sqlite_memory.retrieve(entry_id)
        assert retrieved is not None
        assert retrieved.content == "test entry"
        assert retrieved.entry_type == "test"

    async def test_search(self, sqlite_memory):
        await sqlite_memory.store(
            MemoryEntry(content="Project uses FastAPI", entry_type="project")
        )
        await sqlite_memory.store(
            MemoryEntry(content="Database is SQLite", entry_type="database")
        )

        results = await sqlite_memory.search("FastAPI")
        assert len(results) >= 1
        assert "FastAPI" in results[0].content

    async def test_search_by_type(self, sqlite_memory):
        await sqlite_memory.store(
            MemoryEntry(content="Python 3.12+", entry_type="convention")
        )
        await sqlite_memory.store(
            MemoryEntry(content="User service", entry_type="architecture")
        )

        results = await sqlite_memory.search("Python", entry_type="convention")
        assert len(results) >= 1
        for r in results:
            assert r.entry_type == "convention"

    async def test_delete(self, sqlite_memory):
        entry_id = await sqlite_memory.store(
            MemoryEntry(content="to delete", entry_type="temp")
        )
        deleted = await sqlite_memory.delete(entry_id)
        assert deleted

        retrieved = await sqlite_memory.retrieve(entry_id)
        assert retrieved is None

    async def test_list_by_type(self, sqlite_memory):
        for i in range(3):
            await sqlite_memory.store(
                MemoryEntry(content=f"arch item {i}", entry_type="architecture")
            )

        results = await sqlite_memory.list_by_type("architecture", limit=10)
        assert len(results) >= 3

    async def test_clear(self, sqlite_memory):
        await sqlite_memory.store(
            MemoryEntry(content="something", entry_type="test")
        )
        await sqlite_memory.clear()
        stats = await sqlite_memory.get_stats()
        assert stats["total_entries"] == 0

    async def test_get_stats(self, sqlite_memory):
        stats = await sqlite_memory.get_stats()
        assert stats["backend"] == "sqlite"
        assert "total_entries" in stats
        assert "db_path" in stats
