"""
Director Mode — Mid-Simulation Event Injection

Provides file-based event injection for running simulations.
The API writes events to `{sim_dir}/director_events.json`.
The simulation loop reads and consumes them at each round boundary.
"""

import os
import json
import tempfile
from datetime import datetime
from typing import List, Dict, Any


_DIRECTOR_MARKER = "\n\n# BREAKING EVENT"


def _events_path(simulation_dir: str) -> str:
    return os.path.join(simulation_dir, "director_events.json")


def _history_path(simulation_dir: str) -> str:
    return os.path.join(simulation_dir, "director_events_history.json")


def _atomic_write_json(path: str, data):
    """Write JSON atomically via temp file + rename."""
    dir_name = os.path.dirname(path)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def add_event(simulation_dir: str, event_text: str, round_num: int) -> Dict[str, Any]:
    """
    Queue an event for injection at the next round boundary.

    Args:
        simulation_dir: Path to the simulation data directory.
        event_text: Plain-text description of the event.
        round_num: The round the event was submitted during.

    Returns:
        The event record that was queued.
    """
    event = {
        "id": f"evt_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "event_text": event_text,
        "submitted_at_round": round_num,
        "injected_at_round": None,
        "timestamp": datetime.now().isoformat(),
    }

    path = _events_path(simulation_dir)

    pending = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                pending = json.load(f)
        except (json.JSONDecodeError, OSError):
            pending = []

    pending.append(event)
    _atomic_write_json(path, pending)

    return event


def consume_pending_events(simulation_dir: str, current_round: int) -> List[Dict[str, Any]]:
    """
    Read and clear all pending events. Called by the simulation loop
    at the start of each round.

    Returns:
        List of event dicts that should be injected this round.
    """
    path = _events_path(simulation_dir)

    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            pending = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    if not pending:
        return []

    consumed = []
    for evt in pending:
        evt["injected_at_round"] = current_round
        consumed.append(evt)

    # Clear pending queue
    _atomic_write_json(path, [])

    # Append to history
    _append_history(simulation_dir, consumed)

    return consumed


def _append_history(simulation_dir: str, events: List[Dict[str, Any]]):
    """Append consumed events to the history file."""
    path = _history_path(simulation_dir)
    history = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except (json.JSONDecodeError, OSError):
            history = []

    history.extend(events)
    _atomic_write_json(path, history)


def get_event_history(simulation_dir: str) -> List[Dict[str, Any]]:
    """Return all injected events (history) for this simulation."""
    path = _history_path(simulation_dir)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def get_pending_events(simulation_dir: str) -> List[Dict[str, Any]]:
    """Return events that are queued but not yet injected."""
    path = _events_path(simulation_dir)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def get_event_count(simulation_dir: str) -> int:
    """Return total number of events injected (from history)."""
    return len(get_event_history(simulation_dir))


def inject_director_event_context(agent, event_text: str):
    """
    Inject a breaking event into an agent's system message.
    Uses the same marker-replace pattern as inject_cross_platform_context.

    Args:
        agent: A SocialAgent instance (has .system_message.content).
        event_text: The event text to inject.
    """
    content = agent.system_message.content

    # Remove previous director event section if present
    marker_pos = content.find(_DIRECTOR_MARKER)
    if marker_pos != -1:
        next_marker = content.find("\n\n# ", marker_pos + len(_DIRECTOR_MARKER))
        if next_marker != -1:
            content = content[:marker_pos] + content[next_marker:]
        else:
            content = content[:marker_pos]

    event_block = (
        f"{_DIRECTOR_MARKER}\n"
        f"BREAKING: {event_text}\n"
        f"This is a major new development that just occurred. "
        f"React to this information in your next action — "
        f"it may change your stance, trading behavior, or what you post about."
    )

    agent.system_message.content = content + event_block
