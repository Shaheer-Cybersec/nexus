"""IP / Domain OSINT: resolution, geolocation, and threat flags.

Uses the free ip-api.com service (no key required). Network failures
degrade gracefully so the tool still reports what it can resolve locally.
"""

from __future__ import annotations

import ipaddress
import socket

import requests
from rich.prompt import Prompt
from rich.table import Table

from ..config import get
from ..theme import BOX_TABLE, C_ACC, C_CRIT, C_PRI, C_WARN
from ..ui import console, header, pause

_FIELDS = (
    "status,message,country,countryCode,regionName,city,zip,isp,org,as,"
    "mobile,proxy,hosting,query"
)


def public_ip() -> str | None:
    """Return this machine's public IP via ip-api, or None on failure."""
    try:
        return requests.get("http://ip-api.com/json/?fields=query", timeout=6).json().get("query")
    except Exception:
        return None


def lookup(target: str) -> None:
    """Resolve and enrich a single IP or domain, printing a report table."""
    with console.status(f"[{C_PRI}]Gathering intelligence on [bold]{target}[/bold] …"):
        try:
            resolved = socket.gethostbyname(target)
        except OSError as e:
            console.print(f"[{C_CRIT}]Cannot resolve '{target}': {e}[/]")
            return

        try:
            rdns = socket.gethostbyaddr(resolved)[0]
        except OSError:
            rdns = "N/A"

        try:
            geo = requests.get(f"{get('geo_api')}{resolved}?fields={_FIELDS}", timeout=6).json()
        except Exception:
            geo = {}

    t = Table(box=BOX_TABLE, border_style=C_PRI, show_header=False,
              title=f"[bold {C_PRI}]  OSINT: {target}  [/]")
    t.add_column("Field", style=f"bold {C_PRI}", width=22)
    t.add_column("Value", style="white")

    t.add_row("Target Input", target)
    t.add_row("Resolved IP", f"[bold {C_ACC}]{resolved}[/]")
    t.add_row("Reverse DNS", rdns)

    try:
        ip_obj = ipaddress.ip_address(resolved)
        ip_type = (f"[{C_WARN}]Private / Local[/]" if ip_obj.is_private
                   else f"[{C_ACC}]Public[/]")
        t.add_row("IP Type", ip_type)
    except ValueError:
        pass

    if geo.get("status") == "success":
        t.add_row("Country", f"{geo.get('country', '')} ({geo.get('countryCode', '')})")
        t.add_row("Region", geo.get("regionName", "N/A"))
        t.add_row("City / ZIP", f"{geo.get('city', 'N/A')} / {geo.get('zip', 'N/A')}")
        t.add_row("ISP", geo.get("isp", "N/A"))
        t.add_row("Organization", geo.get("org", "N/A"))
        t.add_row("AS", geo.get("as", "N/A"))

        flags = []
        if geo.get("proxy"):
            flags.append(f"[bold {C_CRIT}]PROXY / VPN DETECTED[/]")
        if geo.get("hosting"):
            flags.append(f"[{C_WARN}]Datacenter / Hosting IP[/]")
        if geo.get("mobile"):
            flags.append(f"[{C_PRI}]Mobile Network[/]")
        t.add_row("Threat Flags", " · ".join(flags) if flags
                  else f"[{C_ACC}]None detected[/]")
    else:
        t.add_row("Geo Data", f"[{C_WARN}]Unavailable (private IP or API error)[/]")

    console.print(t)


def run() -> None:
    """IP / Domain OSINT menu loop."""
    header("IP / DOMAIN OSINT")
    while True:
        console.print(f"[bold {C_PRI}]1[/]  Look up an IP / domain")
        console.print(f"[bold {C_PRI}]2[/]  Look up MY public IP")
        console.print(f"[bold {C_PRI}]3[/]  Back\n")
        choice = Prompt.ask(f"[{C_PRI}]>[/]", choices=["1", "2", "3"])

        if choice == "3":
            break
        if choice == "1":
            target = Prompt.ask(f"[{C_PRI}]Enter IP or domain[/]").strip()
            if target:
                lookup(target)
                pause()
        elif choice == "2":
            with console.status(f"[{C_PRI}]Resolving your public IP …"):
                ip = public_ip()
            if ip:
                console.print(f"Your public IP: [bold {C_ACC}]{ip}[/]\n")
                lookup(ip)
            else:
                console.print(f"[{C_WARN}]Could not determine public IP (offline?).[/]")
            pause()
        console.print()
