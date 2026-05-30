"""Colour palette and shared Rich box styles for the NEXUS interface."""

from __future__ import annotations

from rich import box

# ── Semantic colour roles ──────────────────────────────────────────────
C_PRI = "bright_cyan"      # primary / structural
C_ACC = "bright_green"     # success / good
C_WARN = "bright_yellow"   # warning / caution
C_CRIT = "bright_red"      # critical / danger
C_DIM = "dim white"        # secondary text

# ── Shared box styles ──────────────────────────────────────────────────
BOX_MAIN = box.DOUBLE_EDGE
BOX_TABLE = box.ROUNDED
BOX_SIMPLE = box.SIMPLE


def pct_color(pct: float) -> str:
    """Return a colour for a 0-100 utilisation percentage."""
    if pct > 85:
        return C_CRIT
    if pct > 65:
        return C_WARN
    return C_ACC


def bar(pct: float, width: int = 20, color: str | None = None) -> str:
    """Render a coloured unicode progress bar markup string."""
    pct = max(0.0, min(100.0, pct))
    color = color or pct_color(pct)
    filled = int(pct / 100 * width)
    return f"[{color}]{'█' * filled}{'░' * (width - filled)}[/]"
