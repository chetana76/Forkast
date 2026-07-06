from dataclasses import dataclass

import chromadb

from config.settings import settings
from rag.embeddings import embed_text


@dataclass
class RetrievedDoc:
    doc_id: str
    distance: float
    metadata: dict


class VectorStore:
    """Local ChromaDB-backed vector store. Zero-cost replacement for Vertex AI Vector Search."""

    def __init__(self):
        self._client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        self._collection = self._client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(self, doc_id: str, embedding: list[float], document: str, metadata: dict) -> None:
        self._collection.upsert(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[metadata],
        )

    def query(self, text: str, top_k: int = 5) -> list[RetrievedDoc]:
        query_vector = embed_text(text, task_type="RETRIEVAL_QUERY")
        results = self._collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
        )
        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        return [
            RetrievedDoc(doc_id=i, distance=d, metadata=m or {})
            for i, d, m in zip(ids, distances, metadatas)
        ]

    def query_with_filters(
        self, text: str, allergen_exclusions: list[str], top_k: int = 5
    ) -> list[RetrievedDoc]:
        """Over-fetch then post-filter recipes containing excluded allergens."""
        candidates = self.query(text, top_k=top_k * 3)
        safe = []
        for d in candidates:
            ingredients = " ".join(d.metadata.get("ingredients", [])).lower()
            if not any(allergen in ingredients for allergen in allergen_exclusions):
                safe.append(d)
        return safe[:top_k]


vector_store = VectorStore()
