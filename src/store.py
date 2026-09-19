from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Uses an in-memory store for this lab.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

    def _make_record(self, doc: Document) -> dict[str, Any]:
        # TODO: build a normalized stored record for one document
        metadata = dict(doc.metadata or {})
        metadata.setdefault("doc_id", doc.id)
        metadata.setdefault("id", doc.id)
        return {
            "id": f"{doc.id}:{self._next_index}",
            "doc_id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": self._embedding_fn(doc.content),
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        # TODO: run in-memory similarity search over provided records
        if top_k <= 0:
            return []

        query_embedding = self._embedding_fn(query)
        ranked: list[dict[str, Any]] = []
        for record in records:
            result = {
                "id": record["id"],
                "content": record["content"],
                "metadata": dict(record["metadata"]),
                "score": _dot(query_embedding, record["embedding"]),
            }
            ranked.append(result)

        ranked.sort(key=lambda item: item["score"], reverse=True)
        return ranked[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For in-memory: append dicts to self._store
        """
        # TODO: embed each doc and add to store
        records = []
        for doc in docs:
            record = self._make_record(doc)
            records.append(record)
            self._next_index += 1

        self._store.extend(records)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        # TODO: embed query, compute similarities, return top_k
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        # TODO
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        # TODO: filter by metadata, then search among filtered chunks
        if not metadata_filter:
            return self.search(query, top_k=top_k)

        filtered_records = [
            record
            for record in self._store
            if all(record["metadata"].get(key) == value for key, value in metadata_filter.items())
        ]
        return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        # TODO: remove all stored chunks where metadata['doc_id'] == doc_id
        matching_ids = {
            record["id"]
            for record in self._store
            if record["metadata"].get("doc_id") == doc_id or record.get("doc_id") == doc_id
        }
        if not matching_ids:
            return False

        self._store = [record for record in self._store if record["id"] not in matching_ids]

        return True
