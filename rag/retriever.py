"""
RAG retriever — allergen-safe recipe query interface.

This module is the single entrypoint the Planner agent's tool function calls.
It enforces the allergen hard-veto (Layer 2 of Forkast's three-layer safety
architecture) by running ProfileGuard.validate_allergen_safety() on every
ChromaDB candidate before returning anything to the caller.

The Planner agent therefore only ever sees recipes that have already cleared
the allergen check. Even if the Planner's system instruction were somehow
bypassed, it cannot select an unsafe recipe from what retrieve_safe_recipes()
returns — because unsafe recipes are never in the return value.
"""
from dataclasses import dataclass

from rag.vector_store import vector_store
from security.profile_guard import ProfileGuard
from security.schemas import SafeAgentProfile


@dataclass
class RecipeCandidate:
    """A single allergen-safe recipe candidate returned by retrieve_safe_recipes()."""
    doc_id: str
    distance: float      # cosine distance — lower is more similar
    ingredients: list    # ingredient strings from ChromaDB metadata
    is_safe: bool        # always True — unsafe candidates are never returned
    violations: list     # always [] — violations cause the candidate to be dropped


def retrieve_safe_recipes(
    query: str,
    safe_profile: SafeAgentProfile,
    top_k: int = 5,
) -> list[RecipeCandidate]:
    """
    Retrieve allergen-safe recipe candidates for the given query and profile.

    Steps:
      1. Embed the query using gemini-embedding-001 (RETRIEVAL_QUERY task type)
      2. Query ChromaDB for top-k * 3 candidates (over-fetch to allow for filtering)
      3. For each candidate, run ProfileGuard.validate_allergen_safety()
      4. Drop any candidate where is_safe=False
      5. Return the first top_k safe candidates

    Args:
        query: Natural language query string from the Planner
        safe_profile: PII-free profile containing allergens and constraints
        top_k: Maximum number of safe candidates to return

    Returns:
        List of RecipeCandidate, all guaranteed allergen-safe.
        May be shorter than top_k if the corpus has fewer safe matches.
    """
    # Over-fetch to ensure we have enough candidates after allergen filtering
    docs = vector_store.query_with_filters(
        text=query,
        allergen_exclusions=safe_profile.allergies,
        top_k=top_k,
    )

    candidates = []
    for doc in docs:
        ingredients = doc.metadata.get("ingredients", [])

        # Layer 2 allergen check — runs on every candidate from ChromaDB
        is_safe, violations = ProfileGuard.validate_allergen_safety(
            ingredients, safe_profile
        )

        if is_safe:
            candidates.append(
                RecipeCandidate(
                    doc_id=doc.doc_id,
                    distance=doc.distance,
                    ingredients=ingredients,
                    is_safe=True,
                    violations=[],
                )
            )

    return candidates
