# Forkast — AI-Powered Food Advisor

What's in your pantry, forecast into your next meal.
Multi-Agent RAG system (Google ADK + MCP + Vertex AI Vector Search) for
Kaggle 5-Day Intensive Capstone.

## Setup
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env  # fill in your GCP values
```

## Structure
- `agents/` — Orchestrator, Intake, Inventory (MCP), Planner (RAG), Evaluator (safety check) agents
- `mcp_server/` — Mock pantry/grocery MCP server
- `rag/` — Local ChromaDB ingestion + retrieval (Google AI Studio embeddings, zero-cost)
- `security/` — Profile guard, PII/allergen boundary enforcement
- `observability/` — Local trace logging — zero-cost LangSmith-style observability
- `config/` — Settings and agent config
- `app/` — Streamlit dashboard
- `tests/` — Unit tests
- `notebooks/` — Kaggle submission notebook
