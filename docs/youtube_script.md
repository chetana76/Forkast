# Forkast — YouTube Video Script
## 5-Day AI Agents Intensive Capstone | 5 minutes max

---

### SHOT LIST & TIMING

| Time | Shot | Audio |
|------|------|-------|
| 0:00–0:30 | Face to camera | Hook + problem |
| 0:30–1:00 | Screen: Streamlit UI | Solution intro |
| 1:00–1:45 | Screen: Architecture diagram | Technical walkthrough |
| 1:45–3:15 | Screen: Live Kaggle notebook | Demo — full pipeline run |
| 3:15–3:45 | Screen: ProfileGuard code | Security deep-dive |
| 3:45–4:15 | Screen: Course concepts table | Concepts recap |
| 4:15–4:45 | Screen: GitHub repo | Where to find it |
| 4:45–5:00 | Face to camera | Closing |

---

### FULL SCRIPT

---

**[0:00 — HOOK — face to camera]**

"Imagine you have a severe peanut allergy. You ask an AI assistant for a recipe. It recommends one. You follow it. The third ingredient is peanut butter.

That is not a hypothetical — that is what happens when you trust a prompt to enforce a hard medical constraint. Today I am going to show you Forkast — a multi-agent AI system where allergen safety is enforced in code, not in a prompt."

---

**[0:30 — STREAMLIT UI — screen share]**

"Here is the Forkast dashboard. On the left sidebar, a user enters their profile — allergies, diet type, health conditions, calorie target. For this demo: peanut allergy, anaphylactic severity. Vegetarian. Type 2 diabetes. 1800 calories.

I click Generate Meal Plan. What happens next is not a single LLM call. It is a four-agent pipeline — Intake, Inventory, Planner, and Evaluator — each owning exactly one responsibility."

---

**[1:00 — ARCHITECTURE DIAGRAM — screen share]**

"Here is the architecture. 

At the top: the user submits their profile through the Streamlit UI.

Before any agent sees that data, ProfileGuard runs. It strips the name, email, phone — any PII — and enforces a field whitelist. Agents only ever see allergies, diet type, health flags, and calorie target.

Then the SequentialAgent orchestrator — built on Google's Agent Development Kit — runs four agents in order.

The Intake agent validates the constraints. The Inventory agent calls a real Model Context Protocol server over stdio to query the pantry — it has no access to the profile at all. The Planner agent does RAG retrieval from a local ChromaDB vector store using Gemini embeddings — but before it sees any candidate, a hard allergen veto filters out unsafe recipes in Python. The Evaluator agent independently verifies the Planner's output — it is an LLM-as-Judge safety check that runs after the recipe is written but before the user ever sees it.

Three independent safety layers. None of them are prompts."

---

**[1:45 — KAGGLE NOTEBOOK — screen share, live run]**

"Let me run this in the Kaggle notebook — the actual submission artifact.

Section 3 — ProfileGuard. Watch what happens when I call guard_agent_input on a full UserProfile. The output shows only four fields — allergies, diet type, health flags, calorie target. Name, email, phone: completely absent. That stripping happens in Python before any LLM sees a single token.

Section 5 — the RAG hard-veto. I run retrieve_safe_recipes with a peanut allergy in the profile. Watch the console: you can see it printing recipes being blocked — 'RAG hard-veto: Peanut Butter Banana Smoothie blocked — allergens: peanuts.' That blocking happens before the Planner agent runs, not after.

Now Section 7 — the full demo. I am running the four-agent pipeline end to end.

[pause while pipeline runs]

The pipeline completed. Look at the results:

Intake agent output — structured JSON, no PII.
Planner output — Chickpea Spinach Curry, marked as gluten-free and diabetes-friendly.
Evaluator output — status: APPROVED, reason: recipe contains no allergens and suits the vegetarian and diabetes profile.

Four agents. Three safety layers. One safe recipe."

---

**[3:15 — PROFILEGUARD CODE — screen share]**

"Let me show you why the security architecture is different.

Here is ProfileGuard — a dedicated Python module, not a prompt instruction.

validate_allergen_safety runs in Python and checks every ingredient against every allergen. If any match is found, the recipe is blocked — the Planner never sees it.

enforce_field_whitelist strips any field not explicitly listed in ALLOWED_AGENT_FIELDS. Even if a developer adds a sensitive field to SafeAgentProfile in the future, it cannot reach an agent without updating this whitelist. The failure mode is safe.

scrub_pii uses regex patterns to remove email addresses, phone numbers, and SSN-like patterns from any text before it enters a prompt.

This is what 'security as architecture' looks like. Not a checkbox in a system prompt — actual code that cannot be bypassed by a creative request or a jailbreak."

---

**[3:45 — COURSE CONCEPTS TABLE — screen share]**

"Forkast demonstrates five course concepts from the five-day program.

Day 1 — Autonomous agents and ADK. Four LlmAgents composed into a SequentialAgent — built exactly as taught in the codelabs.

Day 2 — MCP server. The Inventory agent calls a real FastMCP server over stdio transport. You can start it yourself with python -m mcp_server.server.

Day 3 — RAG pipeline. ChromaDB plus gemini-embedding-001 — semantic retrieval with allergen post-filtering. The Planner is grounded in the corpus, not in parametric memory.

Day 4 — Security and guardrails. ProfileGuard, the allergen hard-veto, and the Evaluator agent as LLM-as-Judge. Three independent safety layers.

Day 5 — Production architecture. Streamlit UI, exponential backoff retry for 503 errors, local observability trace logging, model tier separation across two quota buckets."

---

**[4:15 — GITHUB REPO — screen share]**

"Everything is open source at github.com/chetana76/forkast.

The README has full setup instructions — three commands and you are running locally. The entire stack costs zero dollars: Google AI Studio free tier for Gemini and embeddings, local ChromaDB for the vector store, FastMCP for the pantry server.

The notebook — capstone_demo.ipynb — runs on Kaggle with just a GOOGLE_API_KEY secret. No Vertex AI, no billing account, no credit card."

---

**[4:45 — CLOSING — face to camera]**

"Forkast is not just a meal planner. It is a demonstration of what a safe, privacy-preserving personal AI agent looks like when security is designed in from the start.

Four agents. Three safety layers. Zero dollars to run.

Thank you."

---

### RECORDING CHECKLIST

- [ ] Screen resolution: 1920×1080 minimum
- [ ] Record Kaggle notebook in a live session with GOOGLE_API_KEY already in Secrets
- [ ] Have the architecture diagram open in a browser tab (screenshot from chat)
- [ ] Have GitHub repo open and README visible
- [ ] Speak at ~130 words/minute — 5 min = 650 words max
- [ ] Add captions in YouTube Studio after upload
- [ ] Title: "Forkast — AI-Powered Food Advisor | Kaggle 5-Day AI Agents Capstone"
- [ ] Description: include GitHub link and Kaggle competition link
- [ ] Set visibility to Public before submitting to Kaggle

### SCREEN RECORDING TOOLS
- **Mac:** QuickTime Player → New Screen Recording
- **Free alternative:** OBS Studio (obs-project.com)
- **Edit:** iMovie (Mac, free) or DaVinci Resolve (free)
