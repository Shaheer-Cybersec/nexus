"""Network Scout: LAN host discovery and TCP port scanning.

Designed for use only on networks you own or are authorised to test.
"""

from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.prompt import Prompt
from rich.table import Table

from ..config import get
from ..paths import REPORTS_DIR, ensure_dirs
from ..theme import BOX_TABLE, C_ACC, C_CRIT, C_DIM, C_PRI, C_WARN
from ..ui import console, header

# Ports whose exposure typically warrants attention, with a severity tag.
RISKY = {
    21: "HIGH", 23: "CRITICAL", 135: "HIGH", 139: "HIGH", 445: "HIGH",
    1433: "HIGH", 3306: "MEDIUM", 3389: "HIGH", 5432: "MEDIUM",
    5900: "MEDIUM", 4444: "CRITICAL", 6379: "HIGH",
}

COMMON_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 587,
    993, 995, 1433, 1521, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 27017,
]


def local_ip() -> str:
    """Best-effort detection of the primary outbound IPv4 address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def ping(host: str) -> bool:
    """Return True if the host replies to a single ICMP echo."""
    timeout = int(get("ping_timeout_ms"))
    flag = "-n" if os.name == "nt" else "-c"
    wait = ["-w", str(timeout)] if os.name == "nt" else ["-W", str(max(timeout // 1000, 1))]
    try:
        r = subprocess.run(
            ["ping", flag, "1", *wait, host],
            capture_output=True, timeout=max(timeout / 1000 + 1.5, 2),
        )
        return r.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def arp_table() -> dict[str, str]:
    """Parse the OS ARP cache into an {ip: mac} mapping."""
    table: dict[str, str] = {}
    try:
        out = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=5).stdout
        for ip, mac in re.findall(
            r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}"
            r"[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2})",
            out,
        ):
            table[ip] = mac.replace("-", ":").lower()
    except (OSError, subprocess.SubprocessError):
        pass
    return table


def scan_port(host: str, port: int) -> tuple[int, str] | None:
    """Return (port, service) if the TCP port is open, else None."""
    timeout = float(get("port_timeout_s"))
    try:
        with socket.socket() as s:
            s.settimeout(timeout)
            if s.connect_ex((host, port)) == 0:
                try:
                    svc = socket.getservbyport(port)
                except OSError:
                    svc = "unknown"
                return port, svc
    except OSError:
        pass
    return None


def _save_report(name: str, data: dict) -> str:
    ensure_dirs()
    path = REPORTS_DIR / f"{name}_{datetime.now():%Y%m%d_%H%M%S}.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return str(path)


def _discover_hosts(subnet: str, my_ip: str) -> None:
    workers = int(get("scan_threads"))
    live: list[tuple[str, str]] = []
    lock = threading.Lock()

    def check(i: int) -> None:
        ip = f"{subnet}{i}"
        if ping(ip):
            try:
                hn = socket.gethostbyaddr(ip)[0]
            except OSError:
                hn = "—"
            with lock:
                live.append((ip, hn))

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  BarColumn(), TaskProgressColumn(), console=console) as prog:
        task = prog.add_task(f"[{C_PRI}]Sweeping {subnet}1-254 …", total=253)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(check, i) for i in range(1, 254)]
            for fut in futures:
                fut.result()
                prog.advance(task)

    # ARP cache is populated by the sweep — read it afterwards for MACs.
    arp = arp_table()

    if not live:
        console.print(f"[{C_WARN}]No hosts replied — some devices ignore ICMP, "
                      f"or try running as administrator.[/]")
        return

    t = Table(title=f"Live Hosts — {len(live)} found", box=BOX_TABLE, border_style=C_ACC)
    t.add_column("IP", style=f"bold {C_PRI}")
    t.add_column("Hostname", style="white")
    t.add_column("MAC", style=C_DIM)
    t.add_column("Status", style=f"bold {C_ACC}")
    rows = []
    for ip, hn in sorted(live, key=lambda x: [int(p) for p in x[0].split(".")]):
        mac = arp.get(ip, "—")
        marker = "  <- YOU" if ip == my_ip else ""
        t.add_row(ip, hn, mac, f"[{C_ACC}]ONLINE[/]{marker}")
        rows.append({"ip": ip, "hostname": hn, "mac": mac})
    console.print(t)

    if Prompt.ask("Save report?", choices=["y", "n"], default="n") == "y":
        path = _save_report("hostscan", {"subnet": f"{subnet}0/24", "hosts": rows})
        console.print(f"[{C_ACC}]Saved -> {path}[/]")


def _port_scan(target: str) -> None:
    workers = int(get("scan_threads"))
    open_ports: dict[int, str] = {}

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  BarColumn(), TaskProgressColumn(), console=console) as prog:
        task = prog.add_task(f"[{C_PRI}]Scanning {target} …", total=len(COMMON_PORTS))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for result in pool.map(lambda p: scan_port(target, p), COMMON_PORTS):
                if result:
                    open_ports[result[0]] = result[1]
                prog.advance(task)

    try:
        resolved = socket.gethostbyname(target)
    except OSError:
        resolved = target

    t = Table(title=f"Port Scan: {target} ({resolved})", box=BOX_TABLE, border_style=C_PRI)
    t.add_column("Port", style=f"bold {C_PRI}", width=8)
    t.add_column("Service", style="white")
    t.add_column("Status", width=8)
    t.add_column("Risk", width=10)

    if not open_ports:
        console.print(f"[bold {C_ACC}]No common ports open on {target}[/]")
        return

    rows = []
    for port in sorted(open_ports):
        risk = RISKY.get(port, "LOW")
        rc = (C_CRIT if risk == "CRITICAL" else C_WARN if risk == "HIGH"
              else C_PRI if risk == "MEDIUM" else C_ACC)
        t.add_row(str(port), open_ports[port], f"[{C_ACC}]OPEN[/]", f"[bold {rc}]{risk}[/]")
        rows.append({"port": port, "service": open_ports[port], "risk": risk})
    console.print(t)

    if Prompt.ask("Save report?", choices=["y", "n"], default="n") == "y":
        path = _save_report("portscan", {"target": target, "resolved": resolved, "ports": rows})
        console.print(f"[{C_ACC}]Saved -> {path}[/]")


def run() -> None:
    """Network Scout menu loop."""
    header("NETWORK SCOUT")
    my_ip = local_ip()
    subnet = my_ip.rsplit(".", 1)[0] + "."
    console.print(f"Your IP : [bold {C_ACC}]{my_ip}[/]")
    console.print(f"Subnet  : [bold {C_PRI}]{subnet}0/24[/]")
    console.print(f"[{C_DIM}]Only scan networks you own or are authorised to test.[/]\n")

    while True:
        console.print(f"[bold {C_PRI}]1[/]  Discover Live Hosts")
        console.print(f"[bold {C_PRI}]2[/]  Port Scan a Target")
        console.print(f"[bold {C_PRI}]3[/]  Back\n")
        choice = Prompt.ask(f"[{C_PRI}]>[/]", choices=["1", "2", "3"])

        if choice == "3":
            break
        if choice == "1":
            _discover_hosts(subnet, my_ip)
        elif choice == "2":
            target = Prompt.ask(f"[{C_PRI}]Target IP / hostname[/]")
            if target.strip():
                _port_scan(target.strip())
        console.print()
