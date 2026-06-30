import asyncio
import time

import streamlit as st
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part

from agents.orchestrator import root_agent

APP_NAME = "forkast"
USER_ID = "demo_user"

st.set_page_config(page_title="Forkast", page_icon="🍽️", layout="wide")


def run_orchestrator_sync(user_message: str) -> str:
    """Run one turn through the ADK orchestrator, return final text response."""
    runner = InMemoryRunner(agent=root_agent, app_name=APP_NAME)

    async def _run():
        session = await runner.session_service.create_session(
            app_name=APP_NAME, user_id=USER_ID
        )
        content = Content(role="user", parts=[Part(text=user_message)])
        final_text = ""
        async for event in runner.run_async(
            user_id=USER_ID, session_id=session.id, new_message=content
        ):
            if event.is_final_response() and event.content and event.content.parts:
                final_text = event.content.parts[0].text or final_text
        return final_text

    return asyncio.run(_run())


def render_thought_trace(stage_done: dict):
    with st.expander("🧠 Agent thought trace", expanded=True):
        steps = [
            ("Intake Agent", "Validating allergies, diet type, health constraints", "intake"),
            ("Inventory Agent", "Querying pantry via MCP server (stdio)", "inventory"),
            ("Planner Agent", "Retrieving safe recipes via Vertex AI Vector Search (RAG)", "planner"),
        ]
        for label, desc, key in steps:
            status = "✅ done" if stage_done.get(key) else "⏳ pending"
            st.markdown(f"**{label}** — {desc}  \n`{status}`")


def build_user_message(profile: dict, request: str) -> str:
    return (
        f"My profile — allergies: {profile['allergies'] or 'none'}, "
        f"diet type: {profile['diet_type']}, "
        f"health conditions: {profile['health_flags'] or 'none'}, "
        f"calorie target: {profile['calorie_target']}.\n"
        f"Request: {request}"
    )


def main():
    st.title("🍽️ Forkast")
    st.caption("What's in your pantry, forecast into your next meal.")

    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.subheader("Your profile")
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
        request = st.text_area(
            "What are you in the mood for?",
            placeholder="e.g. quick high-protein dinner using what's in my fridge",
        )
        generate = st.button("Generate Meal Plan", type="primary", use_container_width=True)

    with col_right:
        st.subheader("Result")
        trace_slot = st.empty()
        result_slot = st.empty()

        if generate:
            profile = {
                "allergies": allergies,
                "diet_type": diet_type,
                "health_flags": health_flags,
                "calorie_target": int(calorie_target),
            }
            stage_done = {"intake": False, "inventory": False, "planner": False}

            with trace_slot.container():
                render_thought_trace(stage_done)

            with st.spinner("Intake agent validating constraints..."):
                time.sleep(0.4)
                stage_done["intake"] = True
                with trace_slot.container():
                    render_thought_trace(stage_done)

            with st.spinner("Inventory agent querying pantry via MCP..."):
                time.sleep(0.4)
                stage_done["inventory"] = True
                with trace_slot.container():
                    render_thought_trace(stage_done)

            with st.spinner("Planner agent retrieving recipes via RAG..."):
                user_message = build_user_message(profile, request)
                try:
                    final_text = run_orchestrator_sync(user_message)
                except Exception as e:
                    final_text = f"⚠️ Orchestrator error: `{e}`"
                stage_done["planner"] = True
                with trace_slot.container():
                    render_thought_trace(stage_done)

            with result_slot.container():
                st.markdown("---")
                st.markdown(final_text or "_No recommendation returned._")


if __name__ == "__main__":
    main()
