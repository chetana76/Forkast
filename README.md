# 🍴 Forkast — AI-Powered Food Advisor

> **Your kitchen guardian. Allergen-aware. RAG-powered. Agent-driven.**

[![Kaggle](https://img.shields.io/badge/Kaggle-Capstone-blue?logo=kaggle)](https://kaggle.com)
[![Track](https://img.shields.io/badge/Track-Concierge%20Agents-orange)](https://kaggle.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)

---

## The Problem

A recipe app that recommends a dish containing peanuts to someone with anaphylactic allergy is not just unhelpful — **it is dangerous.** Existing meal planners treat allergies as simple filters, not hard architectural boundaries. One hallucinated ingredient in an LLM response can cause a medical emergency.

Forkast is built around one principle: **safety first, meal plan second.**

---

## The Solution

Forkast is a **4-agent RAG pipeline** with an explicit, code-enforced security boundary architecture. Every agent owns exactly one responsibility. No agent can see data it doesn't need. And no recipe reaches the user without passing three independent safety layers.

### Agent Network

| Agent | Responsibility | Model |
|-------|---------------|-------|
| 🧬 **Intake** | Validates user constraints — never sees PII | `gemini-2.5-flash-lite` |
| 📦 **Inventory** | Queries pantry via MCP server (stdio) | `gemini-2.5-flash-lite` |
| 🧠 **Planner** | RAG retrieval from ChromaDB recipe corpus | `gemini-2.5-flash` |
| 🛡️ **Evaluator** | LLM-as-Judge final safety check — APPROVED or REJECTED | `gemini-2.5-flash-lite` |

### Architecture

```
User (Streamlit UI)
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│  ProfileGuard Security Boundary                         │
│  PII stripped · allergens whitelisted · field enforced  │
└─────────────────────────────────────────────────────────┘
        │
        ▼
 SequentialAgent Orchestrator  (deterministic · quota-efficient)
   ┌────┬────────┬────────┬──────────┐
   │    │        │        │          │
   ▼    ▼        ▼        ▼          ▼
Intake  Inventory  Planner  Evaluator
           │          │
           ▼          ▼
       MCP Server  ChromaDB
       (stdio)     + Gemini
                   Embeddings
```

### Three Independent Safety Layers

1. **RAG hard-veto** — allergens filtered from ChromaDB results *before* any LLM sees candidates
2. **ProfileGuard.validate_allergen_safety()** — post-retrieval allergen check on every ingredient
3. **Evaluator agent** — independent LLM-as-Judge verifying the final recipe against all constraints

---

## Course Concepts Demonstrated

| Day | Concept | Where |
|-----|---------|-------|
| Day 1 | Autonomous Agents + ADK | `agents/orchestrator.py` — SequentialAgent with 4 sub-agents |
| Day 2 | MCP Server + Tool Use | `mcp_server/server.py` — FastMCP over stdio transport |
| Day 3 | RAG + Agent Memory | `rag/` — ChromaDB + gemini-embedding-001 + retriever |
| Day 4 | Security + Guardrails | `security/profile_guard.py` — PII stripping, allergen veto, field whitelist |
| Day 5 | Production Architecture | `app/main_app.py` — Streamlit UI, retry backoff, local observability |

---

## Setup

### Prerequisites
- Python 3.11+
- Free Google AI Studio API key → [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/chetana76/forkast.git
cd forkast

# 2. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment
cp .env.example .env
# Edit .env — add your Google AI Studio API key:
# GOOGLE_API_KEY=your-key-here
```

### Run

```bash
# Step 1: Ingest recipe corpus into ChromaDB (run once)
PYTHONPATH=. python -m rag.ingest

# Step 2: Launch Streamlit dashboard
PYTHONPATH=. streamlit run app/main_app.py

# Optional: verify MCP server starts cleanly
PYTHONPATH=. python -m mcp_server.server  # Ctrl+C to exit
```

### Kaggle Notebook

Upload `notebooks/capstone_demo.ipynb` to Kaggle and add `GOOGLE_API_KEY` to Kaggle Secrets (Notebook Settings → Secrets). The notebook is fully self-contained and runs without any local setup.

---

## Project Structure

```
forkast/
├── agents/
│   ├── orchestrator.py       # SequentialAgent — Intake→Inventory→Planner→Evaluator
│   ├── intake_agent.py       # Validates dietary constraints, no PII
│   ├── inventory_agent.py    # MCP client wrapper — pantry queries via stdio
│   ├── planner_agent.py      # RAG-based recipe retrieval + recommendation
│   └── evaluator_agent.py    # LLM-as-Judge safety verification
├── mcp_server/
│   ├── server.py             # FastMCP server entrypoint (stdio transport)
│   ├── tools.py              # get_pantry_items, check_stock implementations
│   └── mock_db.py            # In-memory pantry store from pantry_seed.json
├── rag/
│   ├── embeddings.py         # gemini-embedding-001 via Google AI Studio (free)
│   ├── vector_store.py       # ChromaDB wrapper — cosine similarity, 768d
│   ├── ingest.py             # Corpus chunking + embedding + upsert pipeline
│   └── retriever.py          # Allergen-safe query interface for Planner
├── security/
│   ├── schemas.py            # UserProfile, SafeAgentProfile, Allergy, HealthFlag
│   └── profile_guard.py      # PII stripping, field whitelist, allergen hard-veto
├── observability/
│   └── trace_logger.py       # Local JSONL trace log — zero-cost LangSmith alt
├── app/
│   └── main_app.py           # Streamlit UI with agent trace + retry backoff
├── data/
│   ├── corpus/recipes.json   # 30-recipe RAG corpus
│   └── pantry_seed.json      # Mock pantry with 26 items + expiry dates
├── config/
│   └── settings.py           # Pydantic settings — AI Studio key, model names
├── tests/
│   ├── test_security_boundary.py
│   ├── test_intake_agent.py
│   ├── test_inventory_agent.py
│   └── test_planner_agent.py
├── notebooks/
│   └── capstone_demo.ipynb   # Kaggle submission notebook
├── requirements.txt
├── .env.example
└── README.md
```

---

## Security Architecture

`ProfileGuard` is a dedicated module that enforces PII boundaries at every agent handoff — not a checkbox in a prompt, not a filter that can be bypassed by a clever instruction.

```python
# What the app holds (full UserProfile — contains PII)
profile = UserProfile(
    user_id="user_001",
    name="Chetana Bailur",          # PII
    email="chetana@example.com",    # PII
    allergies=[Allergy(allergen="peanuts", severity=Severity.ANAPHYLACTIC)],
    diet_type=DietType.VEGETARIAN,
    calorie_target=1800,
)

# What agents EVER see (SafeAgentProfile — PII-free, whitelisted)
safe = ProfileGuard.guard_agent_input(profile)
# → {"allergies": ["peanuts"], "diet_type": "vegetarian", "calorie_target": 1800}
# → name, email, user_id: completely absent
```

### Allergen Hard-Veto

```python
# Runs BEFORE any LLM sees recipe candidates
is_safe, violations = ProfileGuard.validate_allergen_safety(
    recipe_ingredients=["pasta", "peanut sauce", "garlic"],
    safe_profile=safe_profile,
)
# → is_safe=False, violations=["peanuts"]
# Recipe never reaches the LLM.
```

---

## Stack

| Component | Technology | Cost |
|-----------|-----------|------|
| LLM calls | Google AI Studio (Gemini 2.5) | Free |
| Embeddings | gemini-embedding-001 | Free |
| Vector store | ChromaDB (local) | Free |
| MCP server | FastMCP over stdio | Free |
| Orchestration | Google ADK (SequentialAgent) | Free |
| UI | Streamlit | Free |
| **Total** | | **$0** |

---

## Demo

Forkast runs a 4-agent pipeline in sequence:

1. **Intake** validates your dietary constraints from the form
2. **Inventory** queries the MCP pantry server for available ingredients
3. **Planner** retrieves allergen-safe recipes from ChromaDB via semantic search
4. **Evaluator** independently verifies the proposed recipe — APPROVED or REJECTED

The Streamlit dashboard shows real per-agent latency, a live observability trace log, and the final APPROVED recipe in a styled card.

---

*Built for the Kaggle 5-Day AI Agents Intensive Capstone | Concierge Agents Track*
*GitHub: [github.com/chetana76/forkast](https://github.com/chetana76/forkast)*
