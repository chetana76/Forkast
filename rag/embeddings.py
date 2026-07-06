from google import genai
from google.genai.types import EmbedContentConfig

from config.settings import settings

_client = genai.Client(api_key=settings.GOOGLE_API_KEY)

# gemini-embedding-001 defaults to 3072 dims; 768 keeps the local Chroma index small and fast.
_OUTPUT_DIM = 768


def embed_text(text: str, task_type: str = "RETRIEVAL_QUERY") -> list[float]:
    response = _client.models.embed_content(
        model=settings.EMBEDDING_MODEL,
        contents=text,
        config=EmbedContentConfig(task_type=task_type, output_dimensionality=_OUTPUT_DIM),
    )
    return response.embeddings[0].values


def embed_batch(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    response = _client.models.embed_content(
        model=settings.EMBEDDING_MODEL,
        contents=texts,
        config=EmbedContentConfig(task_type=task_type, output_dimensionality=_OUTPUT_DIM),
    )
    return [e.values for e in response.embeddings]
