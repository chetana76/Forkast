from google.adk.runners import InMemoryRunner

from agents.orchestrator import root_agent

APP_NAME = "forkast"


def main():
    runner = InMemoryRunner(agent=root_agent, app_name=APP_NAME)
    print(f"{APP_NAME} ADK runner initialized. Wire to CLI/web UI of choice.")
    return runner


if __name__ == "__main__":
    main()
