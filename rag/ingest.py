"""
Corpus ingestion pipeline: chunk recipe/nutrition docs, embed via Google AI Studio,
upsert into local ChromaDB. Run once (or whenever data/corpus/ changes):

    python -m rag.ingest
"""
import json
from pathlib import Path

from rag.embeddings import embed_batch
from rag.vector_store import vector_store

CORPUS_DIR = Path(__file__).resolve().parent.parent / "data" / "corpus"
RECIPES_FILE = CORPUS_DIR / "recipes.json"

# Expected recipes.json shape:
# [
#   {
#     "id": "recipe_001",
#     "title": "Garlic Lemon Chicken",
#     "ingredients": ["chicken breast", "garlic", "lemon", "olive oil"],
#     "steps": ["Season chicken...", "Sear in olive oil...", "..."],
#     "calories": 420,
#     "diet_tags": ["gluten_free"]
#   },
#   ...
# ]


def _doc_text(recipe: dict) -> str:
    return (
        f"{recipe['title']}. "
        f"Ingredients: {', '.join(recipe['ingredients'])}. "
        f"Diet tags: {', '.join(recipe.get('diet_tags', []))}. "
        f"Calories: {recipe.get('calories', 'unknown')}."
    )


def ingest() -> int:
    if not RECIPES_FILE.exists():
        print(f"No corpus found at {RECIPES_FILE}. Add recipes.json first.")
        return 0

    with open(RECIPES_FILE, "r") as f:
        recipes = json.load(f)

    texts = [_doc_text(r) for r in recipes]
    embeddings = embed_batch(texts, task_type="RETRIEVAL_DOCUMENT")

    for recipe, text, embedding in zip(recipes, texts, embeddings):
        vector_store.upsert(
            doc_id=recipe["id"],
            embedding=embedding,
            document=text,
            metadata={
                "title": recipe["title"],
                "ingredients": recipe["ingredients"],
                "steps": recipe.get("steps", []),
                "calories": recipe.get("calories"),
                "diet_tags": recipe.get("diet_tags", []),
            },
        )

    print(f"Ingested {len(recipes)} recipes into '{vector_store._collection.name}'.")
    return len(recipes)


if __name__ == "__main__":
    ingest()
