"""Live system dashboard: resource usage, network throughput, top processes.

Renders a self-refreshing Rich layout until the user presses Ctrl+C.
"""

from __future__ import annotations

import socket
import time
from datetime import datetime

import psutil
from rich.panel import Panel
from rich.table import Table

from ..theme import BOX_MAIN, BOX_SIMPLE, C_ACC, C_CRIT, C_DIM, C_PRI, C_WARN, bar, pct_color
from ..ui import console, header

_GB = 1024 ** 3
_MB = 1024 ** 2


def security_score() -> int:
    """A light-weight heuristic 0-100 'posture' score for the dashboard."""
    import ctypes
    import os

    score = 100
    if psutil.virtual_memory().percent > 85:
        score -= 10
    if psutil.cpu_percent(interval=None) > 80:
        score -= 10
    if psutil.disk_usage("/").percent > 90:
        score -= 10
    try:
        if os.name == "nt" and ctypes.windll.shell32.IsUserAnAdmin():
            score -= 15
    except Exception:
        pass
    return max(score, 0)


def _top_processes(limit: int = 5) -> list[tuple[str, float, float]]:
    """Return the top processes by CPU% as (name, cpu%, mem%)."""
    procs = []
    for p in psutil.process_iter(["name", "cpu_percent", "memory_percent"]):
        try:
            procs.append(
                (
                    p.info["name"] or "?",
                    p.info["cpu_percent"] or 0.0,
                    p.info["memory_percent"] or 0.0,
                )
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    procs.sort(key=lambda x: x[1], reverse=True)
    return procs[:limit]


def _metrics_panel(prev_net, prev_time) -> tuple[Panel, object, float]:
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()
    now = time.time()

    # Throughput since the previous frame.
    dt = max(now - prev_time, 1e-6)
    up_kbps = (net.bytes_sent - prev_net.bytes_sent) / dt / 1024
    dn_kbps = (net.bytes_recv - prev_net.bytes_recv) / dt / 1024

    uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
    sc = security_score()
    sc_color = C_ACC if sc >= 80 else C_WARN if sc >= 60 else C_CRIT
    sc_icon = "[OK]" if sc >= 80 else "[!]" if sc >= 60 else "[X]"

    t = Table(box=BOX_SIMPLE, show_header=False, expand=True, padding=(0, 1))
    t.add_column("Metric", style=f"bold {C_PRI}", width=18)
    t.add_column("Value", style="white", width=32)
    t.add_column("Visual", style="white", width=24)

    t.add_row("CPU", f"[{pct_color(cpu)}]{cpu:.1f}%[/]  ({psutil.cpu_count()} cores)",
              bar(cpu))
    t.add_row("RAM", f"[{pct_color(ram.percent)}]{ram.percent:.1f}%  "
                     f"({ram.used // _MB} / {ram.total // _MB} MB)[/]", bar(ram.percent))
    t.add_row("Disk", f"[{pct_color(disk.percent)}]{disk.percent:.1f}%  "
                      f"({disk.used // _GB} / {disk.total // _GB} GB)[/]", bar(disk.percent))
    t.add_row("Net up/down", f"{up_kbps:7.1f} / {dn_kbps:7.1f} KB/s", "")
    t.add_row("Net total", f"up {net.bytes_sent // _MB} MB   down {net.bytes_recv // _MB} MB", "")
    t.add_row("Uptime", str(uptime).split(".")[0], "")
    t.add_row("Host", f"{socket.gethostname()}  ·  {len(psutil.pids())} procs", "")
    t.add_row("Posture", f"[bold {sc_color}]{sc}/100  {sc_icon}[/]", bar(sc, color=sc_color))

    # Top processes table.
    pt = Table(box=BOX_SIMPLE, show_header=True, expand=True, padding=(0, 1),
               title=f"[{C_DIM}]Top processes by CPU[/]", title_justify="left")
    pt.add_column("Process", style="white")
    pt.add_column("CPU%", justify="right", style=C_WARN, width=8)
    pt.add_column("MEM%", justify="right", style=C_PRI, width=8)
    for name, cpu_p, mem_p in _top_processes():
        pt.add_row(name[:28], f"{cpu_p:.1f}", f"{mem_p:.1f}")

    grid = Table.grid(expand=True)
    grid.add_row(t)
    grid.add_row(pt)

    panel = Panel(
        grid,
        title=f"[bold {C_PRI}]  NEXUS DASHBOARD  ·  {datetime.now():%H:%M:%S}  [/]",
        subtitle=f"[{C_DIM}]Ctrl+C to return[/]",
        border_style=C_PRI,
        box=BOX_MAIN,
    )
    return panel, net, now


def run() -> None:
    """Show the live dashboard until interrupted."""
    from rich.live import Live

    header("SYSTEM DASHBOARD")
    console.print(f"[{C_DIM}]Live feed — Ctrl+C to return[/]\n")

    # Prime cpu_percent so the first frame is meaningful.
    psutil.cpu_percent(interval=None)
    prev_net = psutil.net_io_counters()
    prev_time = time.time()

    try:
        with Live(refresh_per_second=2, screen=False) as live:
            while True:
                panel, prev_net, prev_time = _metrics_panel(prev_net, prev_time)
                live.update(panel)
                time.sleep(1)
    except KeyboardInterrupt:
        pass
