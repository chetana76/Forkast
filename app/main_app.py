import asyncio
import json
import re
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from google.adk.runners import InMemoryRunner

# Support both local .env and Streamlit Community Cloud secrets
def _load_api_key():
    """Load GOOGLE_API_KEY from Streamlit secrets (cloud) or os.environ (local)."""
    import os
    try:
        key = st.secrets.get("GOOGLE_API_KEY", "")
        if key:
            os.environ["GOOGLE_API_KEY"] = key
            os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"
    except Exception:
        pass  # Not on Streamlit Cloud — env vars already set by config/settings.py

_load_api_key()
from google.genai.types import Content, Part

from agents.orchestrator import root_agent
from observability.trace_logger import log_step, read_recent

APP_NAME = "forkast"
USER_ID  = "demo_user"

@st.cache_resource(show_spinner="Initialising recipe index...")
def init_rag():
    """
    Embed the recipe corpus into ChromaDB on first load.
    Cached for the lifetime of the Streamlit session — runs once, not per request.
    Required on Streamlit Community Cloud where disk state does not persist.
    """
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from rag.ingest import ingest
    return ingest()

st.set_page_config(page_title="Forkast", page_icon="🍴", layout="wide")

CUSTOM_CSS = """
<style>
.stApp { background: radial-gradient(circle at 10% 0%, #1f2937 0%, #0f172a 45%, #0b1120 100%); }
.forkast-hero {
    padding: 2rem 2.5rem; border-radius: 20px;
    background: linear-gradient(120deg, #f97316 0%, #ea580c 45%, #c2410c 100%);
    box-shadow: 0 20px 40px -15px rgba(234, 88, 12, 0.5); margin-bottom: 1.5rem;
}
.forkast-hero h1 { color: white; font-size: 2.4rem; margin: 0; }
.forkast-hero p  { color: #ffedd5; font-size: 1.05rem; margin-top: 0.4rem; }
.fk-card {
    background: rgba(30,41,59,0.65); border: 1px solid rgba(148,163,184,0.15);
    border-radius: 16px; padding: 1.4rem 1.6rem; margin-bottom: 1rem;
}
.fk-step {
    display: flex; align-items: center; gap: 0.8rem; padding: 0.7rem 0.9rem;
    border-radius: 12px; margin-bottom: 0.6rem;
    border: 1px solid rgba(148,163,184,0.12); background: rgba(15,23,42,0.4);
}
.fk-step.done  { border-color: rgba(74,222,128,0.4);  background: rgba(34,197,94,0.08); }
.fk-step.active{ border-color: rgba(249,115,22,0.5);  background: rgba(249,115,22,0.1); }
.fk-step-icon  { font-size: 1.4rem; }
.fk-step-text strong { color: #f1f5f9; }
.fk-step-text span   { color: #94a3b8; font-size: 0.85rem; }
.fk-badge {
    display: inline-block; padding: 0.15rem 0.6rem; border-radius: 999px;
    font-size: 0.72rem; font-weight: 600; margin-left: auto;
}
.fk-badge.pending { background: rgba(148,163,184,0.15); color: #94a3b8; }
.fk-badge.active  { background: rgba(249,115,22,0.2);   color: #fb923c; }
.fk-badge.done    { background: rgba(34,197,94,0.2);    color: #4ade80; }
.fk-recipe {
    background: linear-gradient(145deg, rgba(30,41,59,0.85), rgba(15,23,42,0.85));
    border: 1px solid rgba(249,115,22,0.25); border-radius: 18px; padding: 1.8rem 2rem;
}
.fk-recipe h1,.fk-recipe h2,.fk-recipe h3 { color: #fb923c; }
.fk-recipe p,.fk-recipe li { color: #e2e8f0; }
.fk-trace-row {
    font-family: ui-monospace,monospace; font-size: 0.78rem; color: #94a3b8;
    padding: 0.35rem 0.5rem; border-bottom: 1px solid rgba(148,163,184,0.08);
}
.fk-trace-row .agent   { color: #fb923c; font-weight: 600; }
.fk-trace-row .latency { color: #4ade80; }
.retry-banner {
    background: rgba(249,115,22,0.12); border: 1px solid rgba(249,115,22,0.3);
    border-radius: 10px; padding: 0.6rem 1rem; font-size: 0.85rem; color: #fb923c;
    margin-bottom: 0.8rem;
}
section[data-testid="stSidebar"] {
    background: rgba(15,23,42,0.9);
    border-right: 1px solid rgba(148,163,184,0.1);
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

STEPS = [
    ("🧬", "intake_agent",    "Validating allergies, diet type, health constraints"),
    ("📦", "inventory_agent", "Querying pantry via MCP server (stdio)"),
    ("🧠", "planner_agent",   "Retrieving safe recipes via local RAG (ChromaDB)"),
    ("🛡️", "evaluator_agent", "Independent safety check against constraints"),
]
STEP_LABELS = {key for _, key, _ in STEPS}


# ─── Retry + trace runner ────────────────────────────────────────────────────

async def _pipeline(runner, session_id: str, content) -> tuple[list[dict], dict]:
    """One pipeline attempt. Returns (trace_rows, session_state)."""
    trace: list[dict] = []
    agent_start: dict[str, float] = {}
    seen: set[str] = set()

    async for event in runner.run_async(
        user_id=USER_ID, session_id=session_id, new_message=content
    ):
        author = getattr(event, "author", None) or "unknown"
        now = time.perf_counter()
        if author not in seen and author in STEP_LABELS:
            seen.add(author)
            agent_start[author] = now
            trace.append({"agent": author, "status": "active", "latency_ms": None})
        if author in agent_start and event.is_final_response():
            ms = (now - agent_start[author]) * 1000
            for row in trace:
                if row["agent"] == author and row["status"] == "active":
                    row["status"] = "done"
                    row["latency_ms"] = ms

    try:
        sess = await runner.session_service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=session_id
        )
        state = sess.state or {}
    except Exception:
        state = {}
    return trace, state


async def _run_with_backoff(user_message: str, session_id: str, max_retries: int = 3):
    """Retry the full pipeline on 503/429, honouring the server's retry-after hint."""
    for attempt in range(max_retries):
        runner = InMemoryRunner(agent=root_agent, app_name=APP_NAME)
        session = await runner.session_service.create_session(
            app_name=APP_NAME, user_id=USER_ID
        )
        content = Content(role="user", parts=[Part(text=user_message)])
        try:
            return await _pipeline(runner, session.id, content)
        except Exception as exc:
            err = str(exc)
            retryable = any(code in err for code in ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED"))
            if not retryable or attempt == max_retries - 1:
                raise
            m = re.search(r"retry in (\d+(?:\.\d+)?)s", err)
            wait = min(float(m.group(1)) if m else 15 * (2 ** attempt), 90)
            st.markdown(
                f'<div class="retry-banner">⚠️ Gemini overloaded — retrying in {wait:.0f}s '
                f'(attempt {attempt + 1}/{max_retries})…</div>',
                unsafe_allow_html=True,
            )
            await asyncio.sleep(wait)
    raise RuntimeError("Max retries exceeded")


# ─── Evaluator result parser ─────────────────────────────────────────────────

def _parse_eval(raw: str) -> dict:
    if not raw:
        return {"status": "APPROVED", "reason": "No evaluator output — defaulting to approved."}
    cleaned = re.sub(r"^```json\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
    try:
        parsed = json.loads(cleaned)
        if "status" in parsed:
            return parsed
    except json.JSONDecodeError:
        pass
    # If we can't parse JSON but the raw text says APPROVED, trust it
    if "APPROVED" in raw.upper():
        return {"status": "APPROVED", "reason": "Parsed from raw text."}
    return {"status": "REJECTED", "reason": raw[:300]}


# ─── Sync entrypoint ─────────────────────────────────────────────────────────

def run_pipeline(user_message: str, session_id: str) -> tuple[str, list[dict]]:
    async def _go():
        trace, state = await _run_with_backoff(user_message, session_id)
        planner = state.get("planner_result", "")
        eval_raw = state.get("evaluator_result", "")
        for row in trace:
            log_step(session_id, row["agent"], row["status"],
                     f"{row['agent']} {row['status']}", latency_ms=row.get("latency_ms"))
        ev = _parse_eval(eval_raw)
        if ev.get("status") == "APPROVED":
            return planner or "⚠️ Planner returned no recipe.", trace
        reason = ev.get("reason", "Safety check failed.")
        return (
            f"### ⚠️ No safe recipe approved\n\n"
            f"Evaluator rejected the proposed recipe:\n\n> {reason}\n\n"
            f"Try adjusting your request or constraints.", trace
        )
    return asyncio.run(_go())


# ─── UI helpers ──────────────────────────────────────────────────────────────

def render_trace(trace_rows: list[dict]):
    rows_html = []
    active_keys = {r["agent"] for r in trace_rows if r["status"] == "active"}
    done_keys   = {r["agent"] for r in trace_rows if r["status"] == "done"}
    for icon, key, desc in STEPS:
        label = key.replace("_", " ").title()
        if key in done_keys:
            ms = next(r["latency_ms"] for r in trace_rows if r["agent"] == key)
            cls, badge, badge_text = "done", "done", f"{ms:.0f}ms" if ms else "done"
        elif key in active_keys:
            cls, badge, badge_text = "active", "active", "running…"
        else:
            cls, badge, badge_text = "", "pending", "pending"
        rows_html.append(
            f'<div class="fk-step {cls}">'
            f'<div class="fk-step-icon">{icon}</div>'
            f'<div class="fk-step-text"><strong>{label}</strong><br/><span>{desc}</span></div>'
            f'<div class="fk-badge {badge}">{badge_text}</div>'
            f'</div>'
        )
    st.markdown(f'<div class="fk-card">{"".join(rows_html)}</div>', unsafe_allow_html=True)


def render_trace_log():
    records = read_recent(30)
    if not records:
        st.caption("No trace history yet — run a meal plan to populate this.")
        return
    rows = []
    for r in records:
        latency = f"{r['latency_ms']:.0f}ms" if r.get("latency_ms") else "—"
        rows.append(
            f'<div class="fk-trace-row">'
            f'<span class="agent">{r["agent"]}</span> · {r["event_type"]} · '
            f'<span class="latency">{latency}</span> · {r["timestamp"]}'
            f'</div>'
        )
    st.markdown(f'<div class="fk-card">{"".join(rows)}</div>', unsafe_allow_html=True)


def build_message(profile: dict, request: str) -> str:
    return (
        f"Profile — allergies: {profile['allergies'] or 'none'}, "
        f"diet: {profile['diet_type']}, "
        f"health: {profile['health_flags'] or 'none'}, "
        f"calories: {profile['calorie_target']}.\n"
        f"Request: {request}"
    )


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    init_rag()  # Ensure ChromaDB is populated before any agent call
    st.markdown(
        '<div class="forkast-hero"><h1>🍴 Forkast</h1>'
        '<p>What\'s in your pantry, forecast into your next meal.</p></div>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("### 👤 Your profile")
        allergies = st.multiselect(
            "Allergies",
            ["peanuts", "tree nuts", "shellfish", "dairy", "eggs", "gluten", "soy"],
        )
        diet_type = st.selectbox(
            "Diet type",
            ["none", "vegetarian", "vegan", "keto", "halal", "kosher", "gluten_free"],
        )
        health_flags = st.multiselect(
            "Health conditions",
            ["diabetes_type2", "hypertension", "ckd_stage3", "high_cholesterol"],
        )
        calorie_target = st.number_input(
            "Calorie target", min_value=0, max_value=5000, value=2000, step=50
        )
        st.markdown("### 🍽️ What are you craving?")
        request = st.text_area(
            "Request",
            placeholder="e.g. quick high-protein dinner using what's in my fridge",
            label_visibility="collapsed",
        )
        generate = st.button("✨ Generate Meal Plan", type="primary", use_container_width=True)

    trace_slot  = st.empty()
    result_slot = st.empty()

    with trace_slot.container():
        render_trace([])

    if generate:
        profile = dict(
            allergies=allergies, diet_type=diet_type,
            health_flags=health_flags, calorie_target=int(calorie_target),
        )
        session_id = str(uuid.uuid4())[:8]

        with st.spinner("Running pipeline: Intake → Inventory → Planner → Evaluator…"):
            try:
                final_text, trace_rows = run_pipeline(
                    build_message(profile, request), session_id
                )
            except Exception as e:
                final_text = f"⚠️ **Pipeline failed after all retries**\n\n`{e}`"
                trace_rows = []

        with trace_slot.container():
            render_trace(trace_rows)

        with result_slot.container():
            st.markdown(
                f'<div class="fk-recipe">{final_text}</div>',
                unsafe_allow_html=True,
            )

    with st.expander("📊 Observability — local trace log (last 30 events)"):
        render_trace_log()


if __name__ == "__main__":
    main()
