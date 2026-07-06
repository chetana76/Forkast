# Forkast — AI-Powered Food Advisor
## Your kitchen guardian. Allergen-aware. RAG-powered. Agent-driven.

**Track: Concierge Agents** | **GitHub:** github.com/chetana76/forkast

---

## The Problem Nobody Is Solving Correctly

Imagine you have a severe peanut allergy. You open a popular AI meal planning app, describe your dietary needs, and receive a recipe recommendation. The recipe looks perfect — until you notice the third ingredient: peanut butter. The app filtered for "peanut-free" in its UI, but somewhere between your constraint and the LLM's response, the boundary failed.

This is not a hypothetical. LLMs hallucinate. Prompt instructions are not hard constraints. A recipe app that treats a life-threatening allergy as just another filter is not a safe product.

Existing meal planning tools fail in two ways. First, they treat allergens as soft preferences injected into a prompt and trusted to the LLM's judgment. Second, they generate recipes from parametric memory — meaning the LLM recalls recipes from training, with no grounding in what you actually have available, what is expiring, or what specifically matches your health profile.

Forkast was built to solve both problems from first principles. Not as features added on top of a chat interface, but as the foundational design decisions of the entire system.

---

## Why Agents? Why Not Just a Better Prompt?

A single-prompt approach cannot solve this problem well. A well-crafted system prompt saying "never suggest peanut-containing recipes" works until it does not — until the LLM generates a recipe that subtly includes a peanut-based sauce, or until context pressure causes the constraint to be deprioritized. LLM instruction-following is probabilistic, not guaranteed.

The agent architecture in Forkast enforces separation of concerns at the code level. No single agent has both access to the user's allergen data and the authority to select a recipe. The Intake agent validates constraints. The Inventory agent queries stock. The Planner retrieves recipe candidates from a vector store. The Evaluator independently verifies the result. Four separate LLM calls, four separate system instructions, none of which can override each other.

Agents also enable a real retrieval-augmented generation pipeline. The Planner does not recall recipes from training — it queries a local ChromaDB vector store containing a curated recipe corpus and retrieves semantically relevant candidates. The LLM is a reasoning layer, not the knowledge store. This separation matters for both safety and reliability.

---

## The Solution: Forkast

Forkast is a four-agent multi-agent RAG system built on Google's Agent Development Kit, with a security boundary architecture called ProfileGuard that enforces PII protection and allergen safety at the code level before any agent ever sees user data.

**Step 1 — Intake Agent** receives the user's dietary constraints from the Streamlit form, validates them, and outputs structured JSON. This agent never sees the user's name, email, or any personally identifiable information. That stripping happens in ProfileGuard before the session begins.

**Step 2 — Inventory Agent** queries a pantry database via a real Model Context Protocol server running over stdio transport. It calls two MCP tools — `mcp_get_pantry_items()` and `mcp_check_stock()` — and returns a structured inventory report. This agent has zero access to user profile data. It is a pure data provider.

**Step 3 — Planner Agent** receives validated constraints and the inventory report. It calls a registered function tool that runs semantic similarity search against a ChromaDB vector store containing 30 curated recipes, embedded with Google's `gemini-embedding-001` model at 768 dimensions. Before any candidate is returned, `ProfileGuard.validate_allergen_safety()` runs a hard veto — recipes containing any of the user's allergens are filtered out before the LLM sees them. The Planner selects the best safe candidate and formats a complete markdown recipe.

**Step 4 — Evaluator Agent** independently verifies the proposed recipe against the original constraints — checking allergen safety, diet compliance, health flag compatibility, and grounding. It outputs a structured verdict: `APPROVED` or `REJECTED` with a specific reason. If rejected, the UI surfaces the reason clearly.

The orchestrator is a `SequentialAgent` from Google ADK, not an LLM-routed agent. Since the pipeline is deterministic — always Intake, Inventory, Planner, Evaluator — using an LLM to decide routing would waste an API call. The SequentialAgent runs the pipeline directly, saving quota and reducing latency on the free tier.

---

## Security as Architecture, Not Afterthought

The defining feature of Forkast is that security is a first-class architectural concern, not a prompt instruction.

**PII Stripping.** The `UserProfile` object — which may contain name, email, and phone — is never passed to any agent. `ProfileGuard.to_safe_profile()` converts it to a `SafeAgentProfile` containing only four whitelisted fields: allergies, diet type, health flags, and calorie target. Any payload containing PII fields raises a `ProfileGuardError` immediately.

**Field Whitelist.** Even within the safe profile, only explicitly whitelisted fields can enter an agent's context. `enforce_field_whitelist()` strips everything not in `ALLOWED_AGENT_FIELDS`. If a developer adds a sensitive field to `SafeAgentProfile` in the future, it cannot leak into a prompt without an explicit whitelist update. The failure mode is safe by default.

**Allergen Hard-Veto.** `ProfileGuard.validate_allergen_safety()` runs post-retrieval, before the Planner sees any recipe candidate. It checks every ingredient string against every allergen in the profile. If any allergen appears in any ingredient, the recipe is removed from the candidate list entirely — not flagged, not noted, but blocked. The Planner never knows these recipes existed.

This three-layer approach means that even if one layer fails — if the Planner's instruction is ignored, or the Evaluator makes a wrong call — the other layers still provide protection. Defense in depth, applied to a meal planning app.

---

## Course Concepts Applied

**Day 1 — Autonomous Agents and ADK.** Four `LlmAgent` instances, each with a distinct model, instruction, and `output_key`, are composed into a `SequentialAgent`. Agents communicate through ADK session state — each agent's output is automatically stored and accessible to subsequent agents.

**Day 2 — MCP Server and Tool Use.** The Inventory agent calls tools exposed by a real FastMCP server over stdio transport. The server exposes `get_pantry_items_tool()` and `check_stock_tool()`, which read from an in-memory store loaded from a seed JSON file. The MCP server starts independently with `python -m mcp_server.server`.

**Day 3 — RAG and Agent Memory.** The Planner uses a complete retrieval-augmented generation pipeline. The recipe corpus is pre-indexed using `gemini-embedding-001` embeddings at 768 dimensions, stored in ChromaDB with cosine similarity. At query time, the user's request is embedded with `RETRIEVAL_QUERY` task type and the top-k semantically relevant recipes are retrieved. The Planner's recommendations are always grounded in the corpus, not in parametric memory.

**Day 4 — Security and Guardrails.** ProfileGuard is the central security implementation. The Evaluator agent functions as an LLM-as-Judge guardrail — a separate model evaluating another model's output. It uses `gemini-2.5-flash-lite` to keep costs low while catching safety violations the earlier layers might miss, such as high-sodium preparations for hypertension patients.

**Day 5 — Production Architecture.** The Streamlit application includes exponential backoff retry for Gemini 503/429 errors (reading the server's retry-after hint), a local observability trace logger writing structured JSONL logs for every agent step with real latency measurements, and model tier separation: only the Planner uses `gemini-2.5-flash` (10 RPM), while Intake, Inventory, and Evaluator use `gemini-2.5-flash-lite` (15 RPM, separate quota bucket).

---

## The Build Journey

Forkast began with a clear principle: security architecture comes before agent architecture. Before writing a single agent, `UserProfile`, `SafeAgentProfile`, and `ProfileGuard` were designed and tested. This order shaped every subsequent decision.

The first technical challenge was the model landscape. The project started with `gemini-2.0-flash`, which was shut down June 1, 2026. Then `text-embedding-004` returned 404 errors. Switching to `gemini-embedding-001` with explicit `output_dimensionality=768` resolved the embedding issue. Rate limit errors on `gemini-2.5-flash` led to adopting `SequentialAgent` — eliminating LLM routing overhead reduces API calls per request from five or six to four, fitting within the 10 RPM free-tier limit.

An unexpected ADK behavior: the internal genai client reads `GOOGLE_API_KEY` directly from `os.environ`, not from the Pydantic settings object. Pydantic loads `.env` into its own object without exporting to the OS environment. Explicit `os.environ.setdefault()` calls at settings load time fixed this — a subtle but critical integration detail.

The Evaluator agent was added after analyzing a competitor project that implemented guardrails as Python string matching. String matching catches explicit allergen names but cannot catch cases where a recipe's prose describes a high-sodium preparation for a hypertension patient, or a high-glycemic dessert for a diabetes user. The LLM-as-Judge Evaluator catches semantic violations that pattern matching cannot.

The notebook underwent three rounds of fixes during Kaggle testing: the `asyncio.run()` incompatibility in Jupyter's running event loop (replaced with top-level `await`), an LLM tool hallucination where the Inventory agent invented the name `mcp_get_penti_items` (fixed by naming tools explicitly in the instruction), and a Pydantic V2 deprecation warning for `class Config` (replaced with `model_config = ConfigDict(frozen=True)`).

---

## Results and Demo

A complete end-to-end run for a vegetarian user with diabetes and a peanut allergy:

- **Intake** validates constraints in under two seconds
- **Inventory** queries the MCP server, returning 26 available pantry items with expiry dates
- **Planner** retrieves five allergen-safe RAG candidates and selects the best match — consistently dishes like Chickpea Spinach Curry or Lentil Soup that are diabetes-friendly, vegetarian, and peanut-free
- **Evaluator** returns APPROVED with a specific reason in under three seconds
- **Total latency:** 18–25 seconds end-to-end on the free tier

The Streamlit dashboard shows a pipeline trace with real per-agent latency and a local observability panel with the last 30 JSONL log events.

---

## What Makes Forkast Different

Most AI food apps are wrappers around a single LLM call. Forkast is a multi-agent system where allergen safety is enforced at the code level, retrieval is grounded in a real vector store, and every recipe output is independently verified before the user sees it.

The critical distinction: in Forkast, allergen safety cannot be bypassed by a creative prompt, a jailbreak, or an LLM ignoring an instruction under context pressure. The hard veto runs in Python. The whitelist runs in Python. The PII stripping runs in Python. These are not LLM behaviors — they are code behaviors.

That distinction is the entire design philosophy of Forkast. When personal health information and life-threatening allergies are in the picture, "usually safe" is not good enough.

---

---

## Technical Implementation Details

### Vector Store and RAG Pipeline

The recipe corpus is ingested via `rag/ingest.py`, which converts each recipe into an embeddable text representation combining the title, ingredient list, dietary tags, and calorie count. These documents are embedded using `gemini-embedding-001` with the `RETRIEVAL_DOCUMENT` task type and stored in ChromaDB with cosine similarity as the distance metric. Dimensionality is set to 768 (below the model's 3072 maximum) to keep the index compact without meaningful accuracy loss.

At query time, the user's natural language request is embedded with the `RETRIEVAL_QUERY` task type (a different embedding optimized for asymmetric retrieval) and the nearest neighbors are computed. The system over-fetches by a factor of three to account for allergen filtering: if five safe results are needed, fifteen candidates are retrieved so that the hard-veto has enough candidates to filter through without exhausting the result set.

The metadata stored alongside each embedding includes the full ingredient list as a JSON array, enabling the `validate_allergen_safety()` check to operate on structured data rather than parsing prose. This design decision — storing structured metadata rather than relying on the document text — makes the safety check both faster and more reliable.

### Model Strategy and Quota Management

The free tier imposes strict constraints: `gemini-2.5-flash` is limited to 10 requests per minute, `gemini-2.5-flash-lite` to 15. Forkast manages this through deliberate model assignment and architectural choices.

Only the Planner agent, which performs the most complex reasoning task — selecting the best recipe from retrieved candidates and formatting a detailed markdown output — uses the full `gemini-2.5-flash` model. Intake, Inventory, and Evaluator all use `gemini-2.5-flash-lite`, which is a separate quota bucket. This means a single pipeline run consumes one `gemini-2.5-flash` call and three `gemini-2.5-flash-lite` calls — well-distributed across two quota buckets.

The SequentialAgent eliminates a fifth call that an LLM-routed orchestrator would have consumed — since routing is always identical, encoding it as `SequentialAgent` saves one API call per request.

The application also implements exponential backoff retry with up to three attempts, reading the `retry in Xs` hint from Gemini's 503 error message when available and falling back to 15s, 30s, 60s for other transient errors.

### Observability Without Infrastructure

One of the requirements of a production-grade agent system is observability — knowing which agent ran, what it returned, and how long it took. Commercial solutions like LangSmith require cloud infrastructure and API keys.

Forkast implements a zero-cost alternative: `observability/trace_logger.py` writes one JSON line per agent event to a local `data/traces/trace_log.jsonl` file. Each record includes a timestamp, session ID, agent name, event type (start, end, or error), a human-readable summary, and latency in milliseconds. The `StepTimer` context manager captures real latency on each agent call. The Streamlit UI reads the last 30 records and renders them in a styled panel below the recipe output.

### MCP Server Implementation

The pantry MCP server (`mcp_server/server.py`) uses FastMCP over stdio transport — the same protocol used in the course codelabs. The server exposes two tools to the outside world: `get_pantry_items_tool()`, which returns all items currently in stock along with expiry dates and a list of items expiring within four days, and `check_stock_tool(item_name)`, which performs a case-insensitive substring match against the pantry database and returns the matching item's full record.

The pantry data is loaded from `data/pantry_seed.json` into a `MockPantryDB` in-memory object. In production, this would be replaced with a real grocery API — the MCP interface the Inventory agent calls would remain identical.

---

## User Value and Practical Impact

The Concierge Agents track asks for solutions that keep personal information safe and secure while helping individuals and families. Forkast directly addresses this in three ways.

**Safety for vulnerable users.** The 33 million Americans with food allergies and 38 million with diabetes need more than a filter — they need a hard guarantee. Forkast's architecture provides that.

**Privacy by design.** Forkast never allows an LLM to see a user's name, email, or identifier. Users with health conditions should not have to trust that an AI will not inadvertently expose personal details. ProfileGuard enforces this in code.

**Zero cost to run.** Forkast runs entirely on the Google AI Studio free tier. No subscription, no billing account. The ChromaDB vector store is local; only anonymized recipe queries reach Gemini.

---

## Conclusion

Forkast demonstrates that meaningful safety guarantees do not require enterprise infrastructure. They require disciplined architecture: separation of concerns between agents, a security module enforcing boundaries in code rather than prompts, and an independent verification step.

The four-agent pipeline maps cleanly to the five days of the course: autonomous agents, MCP tool use, RAG retrieval, security guardrails, and production patterns. Together they form a system safer than any individual agent alone.

Fork as in food, cast as in forecast — your kitchen guardian.

---

*Submitted for the Kaggle 5-Day AI Agents Intensive Capstone | Concierge Agents Track*
*Full source: github.com/chetana76/forkast*