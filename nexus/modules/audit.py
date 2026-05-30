"""Security Audit: a local posture health-check with a weighted score.

All checks are read-only and run against the local machine. On Windows it
inspects the firewall, Defender, RDP and SMBv1 state; cross-platform checks
cover privileges, open high-risk ports, suspicious processes and resources.
Reports can be exported to JSON for record-keeping.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
from datetime import datetime

import psutil
from rich.align import Align
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from ..paths import REPORTS_DIR, ensure_dirs
from ..theme import BOX_MAIN, BOX_TABLE, C_ACC, C_CRIT, C_DIM, C_PRI, C_WARN
from ..ui import console, header, pause

SUSPICIOUS = ["netcat", "nc.exe", "ncat", "mimikatz", "meterpreter", "cobaltstrike", "psexec"]
DANGEROUS_PORTS = [21, 23, 135, 139, 445, 3389, 4444]


def _is_admin() -> bool:
    try:
        if os.name == "nt":
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        return os.geteuid() == 0  # type: ignore[attr-defined]
    except Exception:
        return False


def _ps(cmd: str, timeout: int = 8) -> str:
    """Run a PowerShell one-liner and return stdout (Windows only)."""
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                           capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def collect() -> list[dict]:
    """Run all checks and return a list of result dicts."""
    results: list[dict] = []

    def chk(name: str, passed: bool, detail: str, weight: int) -> None:
        results.append({"check": name, "passed": passed, "detail": detail, "weight": weight})

    # Privileges
    chk("Not running as admin/root", not _is_admin(),
        "Elevated rights enlarge the attack surface", 15)

    # High-risk ports listening locally
    open_bad = []
    for p in DANGEROUS_PORTS:
        with socket.socket() as s:
            s.settimeout(0.3)
            if s.connect_ex(("127.0.0.1", p)) == 0:
                open_bad.append(p)
    chk("No high-risk ports open locally", not open_bad,
        f"Open: {open_bad}" if open_bad else "All clear", 20)

    # Suspicious processes
    found = []
    for proc in psutil.process_iter(["name"]):
        try:
            nm = (proc.info["name"] or "").lower()
            if any(s in nm for s in SUSPICIOUS):
                found.append(proc.info["name"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    chk("No suspicious processes", not found,
        f"Found: {found}" if found else "None detected", 15)

    # Resource health
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    chk("RAM usage healthy (<90%)", ram.percent < 90, f"{ram.percent:.1f}%", 5)
    chk("Disk usage healthy (<90%)", disk.percent < 90, f"{disk.percent:.1f}%", 5)
    chk("Process count normal (<350)", len(psutil.pids()) < 350,
        f"{len(psutil.pids())} running", 5)

    # Windows-specific checks
    if os.name == "nt":
        fw = _ps("(Get-NetFirewallProfile | Where-Object Enabled -eq 'True').Count")
        chk("Firewall enabled", fw.isdigit() and int(fw) > 0,
            f"{fw or '?'} profile(s) on", 20)

        av = _ps("(Get-MpComputerStatus).AntivirusEnabled")
        chk("Antivirus enabled", "True" in av, "Microsoft Defender", 10)

        rtp = _ps("(Get-MpComputerStatus).RealTimeProtectionEnabled")
        chk("Real-time protection on", "True" in rtp, "Defender RTP", 10)

        rdp = _ps("(Get-ItemProperty 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server')"
                  ".fDenyTSConnections")
        chk("Remote Desktop disabled", rdp.strip() == "1", "RDP listener", 10)

        smb1 = _ps("(Get-SmbServerConfiguration).EnableSMB1Protocol")
        chk("SMBv1 disabled", "False" in smb1, "Legacy SMBv1 protocol", 10)

    return results


def _render(results: list[dict]) -> tuple[int, int]:
    t = Table(box=BOX_TABLE, border_style=C_PRI,
              title=f"[bold {C_PRI}]  SECURITY AUDIT RESULTS  [/]")
    t.add_column("Check", style="white", width=34)
    t.add_column("Status", width=10)
    t.add_column("Details", style=C_DIM)
    t.add_column("Wt.", style=C_DIM, width=5)

    score = max_score = 0
    for r in results:
        max_score += r["weight"]
        if r["passed"]:
            score += r["weight"]
        status = (f"[bold {C_ACC}]PASS[/]" if r["passed"]
                  else f"[bold {C_CRIT}]FAIL[/]")
        t.add_row(r["check"], status, r["detail"] or "OK", str(r["weight"]))
    console.print(t)
    return score, max_score


def run() -> None:
    """Run the audit, render results, optionally export a report."""
    header("SECURITY AUDIT")
    with console.status(f"[{C_PRI}]Running security checks …"):
        results = collect()

    score, max_score = _render(results)
    pct = score / max_score * 100 if max_score else 0
    sc_color = C_ACC if pct >= 80 else C_WARN if pct >= 60 else C_CRIT
    rating = ("EXCELLENT" if pct >= 90 else "GOOD" if pct >= 75
              else "FAIR" if pct >= 55 else "POOR")

    console.print(Panel(
        Align.center(Text(f"Security Score: {score}/{max_score}  ({pct:.0f}%)  —  {rating}",
                          style=f"bold {sc_color}")),
        border_style=sc_color, box=BOX_MAIN, padding=(0, 4),
    ))

    if Prompt.ask("Export report to JSON?", choices=["y", "n"], default="n") == "y":
        ensure_dirs()
        path = REPORTS_DIR / f"audit_{datetime.now():%Y%m%d_%H%M%S}.json"
        path.write_text(json.dumps({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "score": score, "max_score": max_score,
            "percent": round(pct, 1), "rating": rating, "checks": results,
        }, indent=2), encoding="utf-8")
        console.print(f"[{C_ACC}]Saved -> {path}[/]")

    pause()
