"""NEXUS entry point: interactive menu and command-line dispatch.

Run interactively::

    python -m nexus

Or jump straight to a module::

    python -m nexus --audit
    python -m nexus --module dashboard
"""

from __future__ import annotations

import argparse
import sys

from rich.prompt import Prompt
from rich.table import Table

from . import __version__
from .modules import audit, dashboard, hashtool, network, osint, password, pomodoro, tasks
from .paths import ensure_dirs
from .theme import BOX_TABLE, C_ACC, C_DIM, C_PRI, C_WARN
from .ui import console, show_banner

# (key, label, description, run-callable)
MODULES = [
    ("1", "System Dashboard", "Live CPU / RAM / network / top processes", dashboard.run),
    ("2", "Password Fortress", "Entropy, breach check, crack-time, generators", password.run),
    ("3", "Network Scout", "Discover LAN devices · port-scan a target", network.run),
    ("4", "IP / Domain OSINT", "Geolocate · ISP · reverse DNS · proxy/VPN detect", osint.run),
    ("5", "Hash & Integrity", "Hash files/text · verify checksums · compare files", hashtool.run),
    ("6", "Security Audit", "Local posture check with weighted score & report", audit.run),
    ("7", "Task Nexus", "Priority task manager with due dates", tasks.run),
    ("8", "Pomodoro Timer", "Focus sessions with logging & chime", pomodoro.run),
]

# CLI flag → module key, for non-interactive launches.
_FLAG_TO_KEY = {
    "dashboard": "1", "password": "2", "network": "3", "osint": "4",
    "hash": "5", "audit": "6", "tasks": "7", "pomodoro": "8",
}


def _render_menu() -> None:
    show_banner()
    t = Table(box=BOX_TABLE, border_style=C_PRI, show_header=True,
              title=f"[bold {C_PRI}]  SELECT A MODULE  [/]")
    t.add_column("Key", style=f"bold {C_ACC}", width=5)
    t.add_column("Module", style="bold white", width=22)
    t.add_column("Description", style=C_DIM)
    for key, name, desc, _ in MODULES:
        t.add_row(key, name, desc)
    t.add_row("Q", "Quit", "Exit NEXUS")
    console.print(t)


def interactive() -> None:
    """Run the interactive main menu loop."""
    dispatch = {key: fn for key, _, _, fn in MODULES}
    while True:
        _render_menu()
        choice = Prompt.ask(f"\n[bold {C_PRI}]Choose module[/]").strip().lower()
        if choice in ("q", "quit", "exit"):
            console.print(f"\n[bold {C_PRI}]NEXUS offline. Stay secure.[/]\n")
            return
        if choice in dispatch:
            try:
                dispatch[choice]()
            except KeyboardInterrupt:
                console.print(f"\n[{C_WARN}]Module interrupted.[/]")
        else:
            console.print(f"[{C_WARN}]Invalid choice.[/]")


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and launch NEXUS."""
    parser = argparse.ArgumentParser(
        prog="nexus",
        description="NEXUS — Cyber Intelligence & Productivity Terminal",
    )
    parser.add_argument("-v", "--version", action="version",
                        version=f"NEXUS v{__version__}")
    parser.add_argument("-m", "--module", choices=list(_FLAG_TO_KEY),
                        help="launch a single module then exit")
    # Convenience shorthands, e.g. --audit
    for flag in _FLAG_TO_KEY:
        parser.add_argument(f"--{flag}", dest="shortcut", action="store_const",
                            const=flag, help=argparse.SUPPRESS)

    args = parser.parse_args(argv)
    ensure_dirs()

    target = args.module or args.shortcut
    try:
        if target:
            dispatch = {key: fn for key, _, _, fn in MODULES}
            dispatch[_FLAG_TO_KEY[target]]()
        else:
            interactive()
    except KeyboardInterrupt:
        console.print(f"\n[{C_WARN}]Interrupted. Goodbye.[/]")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
