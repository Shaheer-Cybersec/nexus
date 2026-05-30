"""Centralised filesystem paths for NEXUS user data.

Everything NEXUS persists (config, tasks, audit reports, scan results,
pomodoro stats) lives under a single per-user directory so the tool keeps
the rest of the system clean and is easy to back up or wipe.
"""

from __future__ import annotations

from pathlib import Path

#: Root directory for all NEXUS user data, e.g. ~/.nexus
DATA_DIR: Path = Path.home() / ".nexus"

CONFIG_FILE: Path = DATA_DIR / "config.json"
TASKS_FILE: Path = DATA_DIR / "tasks.json"
POMODORO_LOG: Path = DATA_DIR / "pomodoro_log.json"
REPORTS_DIR: Path = DATA_DIR / "reports"


def ensure_dirs() -> None:
    """Create the data directory tree if it does not yet exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
