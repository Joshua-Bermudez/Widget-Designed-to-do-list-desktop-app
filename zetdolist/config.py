"""Persisted app settings: linked notes, active tab, misc preferences."""
from __future__ import annotations

import json
from pathlib import Path

# ============================================================================
# Config - remembers linked notes + app settings
# ============================================================================

APP_DIR_NAME = "ObsidianCheck"


def get_config_dir() -> Path:
    config_dir = Path.home() / f".{APP_DIR_NAME.lower()}"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_path() -> Path:
    return get_config_dir() / "config.json"


def load_config() -> dict:
    path = get_config_path()
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(data: dict) -> None:
    with open(get_config_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_notes() -> list[dict]:
    """Returns the list of linked notes, migrating the old single-file
    config format ({'todo_file': path}) if that's all that's there."""
    cfg = load_config()
    if "notes" in cfg and cfg["notes"]:
        return cfg["notes"]
    if cfg.get("todo_file"):
        path = cfg["todo_file"]
        notes = [{
            "name": Path(path).stem,
            "path": path,
            "daily_reset": False,
            "last_reset_date": None,
            "streak": 0,
        }]
        set_notes(notes)
        return notes
    return []


def set_notes(notes: list[dict]) -> None:
    cfg = load_config()
    cfg["notes"] = notes
    cfg.pop("todo_file", None)
    save_config(cfg)


def get_active_index() -> int:
    return load_config().get("active_index", 0)


def set_active_index(index: int) -> None:
    cfg = load_config()
    cfg["active_index"] = index
    save_config(cfg)


def get_setting(key: str, default=None):
    return load_config().get(key, default)


def set_setting(key: str, value) -> None:
    cfg = load_config()
    cfg[key] = value
    save_config(cfg)
