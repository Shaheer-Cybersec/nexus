"""Pomodoro Timer: focused work/break cycles with logging and a chime.

Completed work sessions are appended to a JSON log so you can review your
focus history over time.
"""

from __future__ import annotations

import json
import time
from datetime import datetime

from rich.align import Align
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.text import Text

from ..config import get
from ..paths import POMODORO_LOG, ensure_dirs
from ..theme import BOX_MAIN, C_ACC, C_PRI, C_WARN
from ..ui import console, header, pause


def _chime() -> None:
    """Play a short beep on phase change (best-effort, Windows)."""
    if not get("enable_sound"):
        return
    try:
        import winsound
        winsound.Beep(880, 200)
        winsound.Beep(1175, 250)
    except Exception:
        print("\a", end="", flush=True)  # terminal bell fallback


def _log_session(label: str, minutes: int) -> None:
    ensure_dirs()
    log = []
    if POMODORO_LOG.exists():
        try:
            log = json.loads(POMODORO_LOG.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            log = []
    log.append({
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "label": label, "minutes": minutes,
    })
    POMODORO_LOG.write_text(json.dumps(log, indent=2), encoding="utf-8")


def _countdown(phase: str, minutes: int, session: int, total_sessions: int, color: str) -> bool:
    """Run one timed phase. Returns False if the user cancelled."""
    total = minutes * 60
    try:
        from rich.live import Live
        with Live(refresh_per_second=1, screen=False) as live:
            for remaining in range(total, 0, -1):
                mins, secs = divmod(remaining, 60)
                pct = (total - remaining) / total * 100
                blocks = int(pct / 2.5)
                live.update(Panel(
                    Align.center(Text(
                        f"{mins:02d}:{secs:02d}\n\n" + "█" * blocks + "░" * (40 - blocks),
                        style=f"bold {color}")),
                    title=f"[bold {color}]  {phase} — Session {session}/{total_sessions}  [/]",
                    border_style=color, box=BOX_MAIN,
                ))
                time.sleep(1)
        return True
    except KeyboardInterrupt:
        return False


def run() -> None:
    """Pomodoro Timer entry point."""
    header("POMODORO TIMER")
    work = IntPrompt.ask(f"[{C_PRI}]Work duration (min)[/]",
                         default=int(get("default_pomodoro_work")))
    brk = IntPrompt.ask(f"[{C_PRI}]Break duration (min)[/]",
                        default=int(get("default_pomodoro_break")))
    rounds = IntPrompt.ask(f"[{C_PRI}]Number of sessions[/]",
                           default=int(get("default_pomodoro_rounds")))
    task = Prompt.ask(f"[{C_PRI}]What are you focusing on? (optional)[/]", default="").strip()

    for session in range(1, rounds + 1):
        if not _countdown("WORK", work, session, rounds, C_ACC):
            console.print(f"[{C_WARN}]Timer cancelled.[/]")
            return
        _chime()
        _log_session(task or "Focus session", work)

        if session < rounds:
            console.print(f"[bold {C_ACC}]Session {session} done — take a break.[/]")
            if not _countdown("BREAK", brk, session, rounds, C_WARN):
                console.print(f"[{C_WARN}]Timer cancelled.[/]")
                return
            _chime()

    console.print(Panel(
        Align.center(Text(f"All {rounds} Pomodoros complete! Logged {rounds * work} focus minutes.",
                          style=f"bold {C_ACC}")),
        border_style=C_ACC, box=BOX_MAIN,
    ))
    pause()
