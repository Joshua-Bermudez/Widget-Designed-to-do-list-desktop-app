"""Per-day completion log, used to power the "times completed" chart."""
from __future__ import annotations

import json
from pathlib import Path

from .config import get_config_dir

# ============================================================================
# Completion history - logs which daily tasks were checked off each day,
# so a chart can show how many times each one has been finished
# ============================================================================

def get_history_path() -> Path:
    return get_config_dir() / "history.json"


def load_history() -> dict:
    path = get_history_path()
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_history(data: dict) -> None:
    with open(get_history_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def record_completions(note_path: str, day: str, task_texts: list[str]) -> None:
    """Logs which tasks were checked off on `day` for a daily-reset note.
    Called right before the daily reset clears the checkboxes."""
    history = load_history()
    history.setdefault(note_path, {})[day] = task_texts
    save_history(history)


def get_completion_counts(note_path: str) -> dict[str, int]:
    """Returns {task_text: total times completed} across all logged days
    for one note."""
    counts: dict[str, int] = {}
    for texts in load_history().get(note_path, {}).values():
        for text in texts:
            counts[text] = counts.get(text, 0) + 1
    return counts
