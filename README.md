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
- `agents/` — Orchestrator, Intake, Inventory (MCP), Planner (RAG) agents
- `mcp_server/` — Mock pantry/grocery MCP server
- `rag/` — Vertex AI Vector Search ingestion + retrieval
- `security/` — Profile guard, PII/allergen boundary enforcement
- `config/` — Settings and agent config
- `tests/` — Unit tests
- `notebooks/` — Kaggle submission notebook
