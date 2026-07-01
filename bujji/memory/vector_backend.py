import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from bujji.core.models import MemoryEntry
from bujji.memory.base import MemoryBackend


class VectorMemory(MemoryBackend):
    """ChromaDB-based vector semantic memory."""

    def __init__(
        self,
        chroma_path: str,
        collection_name: str = "bujji_memory",
    ) -> None:
        self.chroma_path = str(Path(chroma_path).expanduser().resolve())
        Path(self.chroma_path).mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self._client: Optional[chromadb.Client] = None
        self._collection: Optional[chromadb.Collection] = None

    def _get_client(self) -> chromadb.Client:
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=self.chroma_path,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._client

    def _get_collection(self) -> chromadb.Collection:
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    async def store(self, entry: MemoryEntry) -> str:
        entry_id = entry.id or str(uuid.uuid4())
        collection = self._get_collection()

        metadata = {
            **entry.metadata,
            "entry_type": entry.entry_type,
            "timestamp": entry.timestamp.isoformat(),
            "content_preview": entry.content[:200],
        }

        collection.add(
            documents=[entry.content],
            metadatas=[metadata],
            ids=[entry_id],
        )
        return entry_id

    async def retrieve(self, entry_id: str) -> Optional[MemoryEntry]:
        collection = self._get_collection()
        try:
            result = collection.get(ids=[entry_id])
        except Exception:
            return None

        if not result["ids"]:
            return None

        return MemoryEntry(
            id=result["ids"][0],
            content=result["documents"][0],
            metadata=result["metadatas"][0] if result["metadatas"] else {},
            timestamp=datetime.fromisoformat(
                result["metadatas"][0].get("timestamp", datetime.now(timezone.utc).isoformat())
            )
            if result["metadatas"]
            else datetime.now(timezone.utc),
            entry_type=result["metadatas"][0].get("entry_type", "general")
            if result["metadatas"]
            else "general",
        )

    async def search(
        self,
        query: str,
        limit: int = 10,
        entry_type: Optional[str] = None,
    ) -> list[MemoryEntry]:
        collection = self._get_collection()

        where: Optional[dict[str, Any]] = None
        if entry_type:
            where = {"entry_type": entry_type}

        results = collection.query(
            query_texts=[query],
            n_results=limit,
            where=where,
        )

        entries = []
        for i in range(len(results["ids"][0])):
            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            entries.append(
                MemoryEntry(
                    id=results["ids"][0][i],
                    content=results["documents"][0][i],
                    metadata=metadata,
                    timestamp=datetime.fromisoformat(
                        metadata.get("timestamp", datetime.now(timezone.utc).isoformat())
                    ),
                    entry_type=metadata.get("entry_type", "general"),
                )
            )
        return entries

    async def delete(self, entry_id: str) -> bool:
        collection = self._get_collection()
        try:
            collection.delete(ids=[entry_id])
            return True
        except Exception:
            return False

    async def list_by_type(
        self,
        entry_type: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MemoryEntry]:
        collection = self._get_collection()
        results = collection.get(
            where={"entry_type": entry_type},
            limit=limit,
            offset=offset,
        )

        entries = []
        for i in range(len(results["ids"])):
            metadata = results["metadatas"][i] if results["metadatas"] else {}
            entries.append(
                MemoryEntry(
                    id=results["ids"][i],
                    content=results["documents"][i],
                    metadata=metadata,
                    timestamp=datetime.fromisoformat(
                        metadata.get("timestamp", datetime.now(timezone.utc).isoformat())
                    ),
                    entry_type=metadata.get("entry_type", "general"),
                )
            )
        return entries

    async def clear(self) -> None:
        client = self._get_client()
        try:
            client.delete_collection(self.collection_name)
        except Exception:
            pass
        self._collection = None

    async def get_stats(self) -> dict[str, Any]:
        collection = self._get_collection()
        count = collection.count()
        return {
            "backend": "chromadb",
            "total_entries": count,
            "collection": self.collection_name,
            "chroma_path": self.chroma_path,
        }
