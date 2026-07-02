from typing import Any

from bujji.core.config import Settings
from bujji.core.exceptions import MemoryError
from bujji.core.models import MemoryEntry
from bujji.memory.sqlite_backend import SQLiteMemory
from bujji.memory.vector_backend import VectorMemory


class MemoryManager:
    """Orchestrates memory operations across backends."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._sqlite: SQLiteMemory | None = None
        self._vector: VectorMemory | None = None
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return

        self._sqlite = SQLiteMemory(self.settings.memory.sqlite_path)
        self._vector = VectorMemory(
            chroma_path=self.settings.memory.chroma_path,
            collection_name=self.settings.memory.vector_collection,
        )
        self._initialized = True

    async def store(
        self,
        content: str,
        entry_type: str = "general",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        await self._ensure_initialized()
        entry = MemoryEntry(
            content=content,
            entry_type=entry_type,
            metadata=metadata or {},
        )
        sqlite_id = await self._sqlite.store(entry)
        entry.id = sqlite_id
        try:
            await self._vector.store(entry)
        except Exception as e:
            raise MemoryError(f"Vector store failed: {e}") from e
        return sqlite_id

    async def search(
        self,
        query: str,
        limit: int = 10,
        entry_type: str | None = None,
        semantic: bool = True,
    ) -> list[MemoryEntry]:
        await self._ensure_initialized()

        if semantic:
            try:
                results = await self._vector.search(query, limit, entry_type)
                if results:
                    return results
            except Exception:
                pass

        return await self._sqlite.search(query, limit, entry_type)

    async def retrieve(self, entry_id: str) -> MemoryEntry | None:
        await self._ensure_initialized()
        return await self._sqlite.retrieve(entry_id)

    async def delete(self, entry_id: str) -> bool:
        await self._ensure_initialized()
        sqlite_ok = await self._sqlite.delete(entry_id)
        await self._vector.delete(entry_id)
        return sqlite_ok

    async def list_by_type(
        self,
        entry_type: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MemoryEntry]:
        await self._ensure_initialized()
        return await self._sqlite.list_by_type(entry_type, limit, offset)

    async def clear(self) -> None:
        await self._ensure_initialized()
        await self._sqlite.clear()
        await self._vector.clear()

    async def get_stats(self) -> dict[str, Any]:
        await self._ensure_initialized()
        sqlite_stats = await self._sqlite.get_stats()
        vector_stats = await self._vector.get_stats()
        return {"sqlite": sqlite_stats, "chromadb": vector_stats}

    async def _ensure_initialized(self) -> None:
        if not self._initialized:
            await self.initialize()
