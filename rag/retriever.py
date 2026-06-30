from dataclasses import dataclass

from rag.vector_store import vector_store
from security.profile_guard import ProfileGuard
from security.schemas import SafeAgentProfile


@dataclass
class RecipeCandidate:
    doc_id: str
    distance: float
    ingredients: list[str]
    is_safe: bool
    violations: list[str]


def retrieve_safe_recipes(
    query: str,
    safe_profile: SafeAgentProfile,
    top_k: int = 5,
) -> list[RecipeCandidate]:
    """Single entrypoint for planner_agent: retrieve + hard-veto unsafe recipes."""
    docs = vector_store.query_with_filters(
        text=query,
        allergen_exclusions=safe_profile.allergies,
        top_k=top_k,
    )

    candidates: list[RecipeCandidate] = []
    for doc in docs:
        ingredients = doc.metadata.get("ingredients", [])
        is_safe, violations = ProfileGuard.validate_allergen_safety(ingredients, safe_profile)
        candidates.append(
            RecipeCandidate(
                doc_id=doc.doc_id,
                distance=doc.distance,
                ingredients=ingredients,
                is_safe=is_safe,
                violations=violations,
            )
        )
    return [c for c in candidates if c.is_safe]
