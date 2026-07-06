"""
Zero-cost local observability — replaces LangSmith-style tracing.
Logs one JSON line per agent step: who ran, what they returned, how long it took.
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from config.settings import settings

_LOG_PATH = Path(settings.TRACE_LOG_PATH)


def _ensure_log_dir() -> None:
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def log_step(
    session_id: str,
    agent_name: str,
    event_type: str,
    summary: str,
    latency_ms: Optional[float] = None,
    extra: Optional[dict[str, Any]] = None,
) -> None:
    """Append one trace record. Never raises — observability must not break the app."""
    try:
        _ensure_log_dir()
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "agent": agent_name,
            "event_type": event_type,  # "start" | "end" | "error"
            "summary": summary[:500],
            "latency_ms": latency_ms,
            "extra": extra or {},
        }
        with open(_LOG_PATH, "a") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass  # observability is best-effort, never blocks the main flow


def read_recent(n: int = 20) -> list[dict[str, Any]]:
    """Read the last n trace records, most recent first."""
    if not _LOG_PATH.exists():
        return []
    with open(_LOG_PATH, "r") as f:
        lines = f.readlines()
    records = []
    for line in lines[-n:]:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(records))


class StepTimer:
    """Context manager: log a start/end pair with latency for one agent step."""

    def __init__(self, session_id: str, agent_name: str):
        self.session_id = session_id
        self.agent_name = agent_name
        self._start = None

    def __enter__(self):
        self._start = time.perf_counter()
        log_step(self.session_id, self.agent_name, "start", f"{self.agent_name} started")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        latency_ms = (time.perf_counter() - self._start) * 1000
        if exc_type is not None:
            log_step(
                self.session_id, self.agent_name, "error",
                f"{exc_type.__name__}: {exc_val}", latency_ms=latency_ms,
            )
        else:
            log_step(
                self.session_id, self.agent_name, "end",
                f"{self.agent_name} completed", latency_ms=latency_ms,
            )
        return False
