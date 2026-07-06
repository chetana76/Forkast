# Forkast — Security Context Document

## Project Purpose
Forkast is a meal recommendation agent that prioritises allergen safety and user privacy
above all other concerns. This document defines the security rules every agent and module
must follow. It is the authoritative source for any AI assistant scaffolding or modifying
this codebase.

## Hard Security Rules (never override)

1. **No agent ever receives a raw UserProfile object.** The only permitted path is
   `ProfileGuard.guard_agent_input(profile)` → `SafeAgentProfile` → whitelisted dict.

2. **PII fields are permanently blocked from agent context:**
   `name`, `email`, `phone`, `address`, `ssn`, `date_of_birth`
   Any payload containing these keys raises `ProfileGuardError` immediately.

3. **Allergen safety has three independent enforcement layers:**
   - Layer 1: RAG hard-veto in `rag/retriever.py` — unsafe recipes never reach the LLM
   - Layer 2: `ProfileGuard.validate_allergen_safety()` — post-retrieval ingredient check
   - Layer 3: Evaluator agent — LLM-as-Judge final verification
   All three must remain independent. No layer may bypass another.

4. **Agents have strict single responsibility:**
   - Intake: validates constraints only — never plans meals
   - Inventory: queries pantry only — never sees user profile
   - Planner: retrieves and recommends only — never approves own output
   - Evaluator: verifies only — never generates recipes

5. **GOOGLE_API_KEY must never appear in source code.** Always load from `.env`
   via `pydantic-settings`. The `.env` file is in `.gitignore`.

## Permitted Agent Data Access
| Agent | Can see |
|-------|---------|
| Intake | Raw user message (already PII-scrubbed by caller) |
| Inventory | Pantry MCP server output only |
| Planner | SafeAgentProfile (whitelisted fields) + inventory result + RAG output |
| Evaluator | SafeAgentProfile (whitelisted fields) + planner_result |

## Model Assignment
| Agent | Model | Reason |
|-------|-------|--------|
| Planner | gemini-2.5-flash | Complex reasoning — needs full capability |
| Intake, Inventory, Evaluator | gemini-2.5-flash-lite | Structured tasks — separate quota bucket |
| Embeddings | gemini-embedding-001 | Only viable embedding model on free tier |
