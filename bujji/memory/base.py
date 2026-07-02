from abc import ABC, abstractmethod
from typing import Any

from bujji.core.models import MemoryEntry


class MemoryBackend(ABC):
    """Abstract base for memory storage backends."""

    @abstractmethod
    async def store(self, entry: MemoryEntry) -> str:
        """Store a memory entry and return its ID."""

    @abstractmethod
    async def retrieve(self, entry_id: str) -> MemoryEntry | None:
        """Retrieve a memory entry by ID."""

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 10,
        entry_type: str | None = None,
    ) -> list[MemoryEntry]:
        """Search memory entries."""

    @abstractmethod
    async def delete(self, entry_id: str) -> bool:
        """Delete a memory entry."""

    @abstractmethod
    async def list_by_type(
        self,
        entry_type: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MemoryEntry]:
        """List entries by type."""

    @abstractmethod
    async def clear(self) -> None:
        """Clear all memory entries."""

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]:
        """Get memory storage statistics."""
