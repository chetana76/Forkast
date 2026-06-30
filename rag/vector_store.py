from dataclasses import dataclass

from google.cloud import aiplatform

from config.settings import settings
from rag.embeddings import embed_text


@dataclass
class RetrievedDoc:
    doc_id: str
    distance: float
    metadata: dict


class VectorStore:
    """Thin wrapper over a deployed Vertex AI Vector Search index."""

    def __init__(self):
        aiplatform.init(
            project=settings.GOOGLE_CLOUD_PROJECT,
            location=settings.GOOGLE_CLOUD_LOCATION,
        )
        self._endpoint = aiplatform.MatchingEngineIndexEndpoint(
            index_endpoint_name=settings.VECTOR_ENDPOINT_ID
        )

    def query(self, text: str, top_k: int = 5) -> list[RetrievedDoc]:
        query_vector = embed_text(text, task_type="RETRIEVAL_QUERY")
        results = self._endpoint.find_neighbors(
            deployed_index_id=settings.VECTOR_DEPLOYED_INDEX_ID,
            queries=[query_vector],
            num_neighbors=top_k,
        )
        neighbors = results[0] if results else []
        return [
            RetrievedDoc(doc_id=n.id, distance=n.distance, metadata={})
            for n in neighbors
        ]

    def query_with_filters(
        self, text: str, allergen_exclusions: list[str], top_k: int = 5
    ) -> list[RetrievedDoc]:
        """Over-fetch then post-filter recipes containing excluded allergens by doc_id naming
        convention (doc_id encodes ingredient slug). Replace with native numeric/restrict
        filters once the index schema is finalized."""
        candidates = self.query(text, top_k=top_k * 3)
        safe = [
            d for d in candidates
            if not any(allergen in d.doc_id.lower() for allergen in allergen_exclusions)
        ]
        return safe[:top_k]


vector_store = VectorStore()
