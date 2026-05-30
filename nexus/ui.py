"""Shared UI primitives: the console, banner, and small helpers.

A single Console instance is shared across every module so colours,
width detection and recording all behave consistently.
"""

from __future__ import annotations

import os

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

from . import __version__
from .theme import BOX_MAIN, C_ACC, C_DIM, C_PRI

console = Console()

BANNER = r"""
  ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗
  ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝
  ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗
  ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║
  ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║
  ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
"""


def clear() -> None:
    """Clear the terminal screen, cross-platform."""
    os.system("cls" if os.name == "nt" else "clear")


def show_banner() -> None:
    """Render the NEXUS splash banner."""
    clear()
    t = Text(BANNER, style=f"bold {C_PRI}")
    t.append("\n  Cyber Intelligence & Productivity Terminal", style=f"dim {C_PRI}")
    t.append(f"   v{__version__}\n", style=f"bold {C_ACC}")
    console.print(
        Panel(Align.center(t), border_style=C_PRI, box=BOX_MAIN, padding=(0, 6))
    )


def header(title: str) -> None:
    """Print a section header rule."""
    console.print()
    console.print(Rule(f"[bold {C_PRI}]  {title}  [/]", style=C_PRI))
    console.print()


def pause() -> None:
    """Wait for the user to press Enter."""
    console.print(f"\n[{C_DIM}]Press Enter to continue...[/]", end="")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass
