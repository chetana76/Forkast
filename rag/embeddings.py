from google import genai
from google.genai.types import EmbedContentConfig

from config.settings import settings

_client = genai.Client(
    vertexai=True,
    project=settings.GOOGLE_CLOUD_PROJECT,
    location=settings.GOOGLE_CLOUD_LOCATION,
)


def embed_text(text: str, task_type: str = "RETRIEVAL_QUERY") -> list[float]:
    response = _client.models.embed_content(
        model=settings.EMBEDDING_MODEL,
        contents=text,
        config=EmbedContentConfig(task_type=task_type),
    )
    return response.embeddings[0].values


def embed_batch(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    response = _client.models.embed_content(
        model=settings.EMBEDDING_MODEL,
        contents=texts,
        config=EmbedContentConfig(task_type=task_type),
    )
    return [e.values for e in response.embeddings]
