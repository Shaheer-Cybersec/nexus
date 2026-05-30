"""User configuration handling for NEXUS.

Settings are stored as JSON under the user data directory. Missing keys
fall back to sane defaults so the tool always runs even with a partial or
absent config file.
"""

from __future__ import annotations

import json
from typing import Any

from .paths import CONFIG_FILE, ensure_dirs

DEFAULTS: dict[str, Any] = {
    "scan_threads": 100,          # parallel workers for network sweeps
    "ping_timeout_ms": 500,       # per-host ping timeout
    "port_timeout_s": 0.5,        # per-port connect timeout
    "default_pomodoro_work": 25,  # minutes
    "default_pomodoro_break": 5,  # minutes
    "default_pomodoro_rounds": 4,
    "password_length": 20,
    "enable_sound": True,         # beep on pomodoro phase change (Windows)
    "geo_api": "http://ip-api.com/json/",
}


def load_config() -> dict[str, Any]:
    """Load config merged over defaults (defaults win for missing keys)."""
    cfg = dict(DEFAULTS)
    if CONFIG_FILE.exists():
        try:
            cfg.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            pass  # corrupt config → fall back to defaults silently
    return cfg


def save_config(cfg: dict[str, Any]) -> None:
    """Persist the given config dict to disk."""
    ensure_dirs()
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def get(key: str) -> Any:
    """Convenience accessor for a single config value."""
    return load_config().get(key, DEFAULTS.get(key))
