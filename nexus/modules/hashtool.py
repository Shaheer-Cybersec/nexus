"""Hash & File Integrity Toolkit.

Compute cryptographic digests of files or text, verify a file against an
expected checksum, and compare two files for byte-level equality — handy
for validating downloads and spotting tampering.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from rich.prompt import Prompt
from rich.table import Table

from ..theme import BOX_TABLE, C_ACC, C_CRIT, C_DIM, C_PRI, C_WARN
from ..ui import console, header, pause

ALGOS = ["md5", "sha1", "sha256", "sha512"]
_CHUNK = 1 << 20  # 1 MiB streaming read


def hash_file(path: Path, algos: list[str] = ALGOS) -> dict[str, str]:
    """Return {algo: hexdigest} for a file, streamed so large files are fine."""
    digests = {a: hashlib.new(a) for a in algos}
    with path.open("rb") as f:
        while chunk := f.read(_CHUNK):
            for h in digests.values():
                h.update(chunk)
    return {a: h.hexdigest() for a, h in digests.items()}


def hash_text(text: str, algos: list[str] = ALGOS) -> dict[str, str]:
    """Return {algo: hexdigest} for a UTF-8 string."""
    data = text.encode("utf-8")
    return {a: hashlib.new(a, data).hexdigest() for a in algos}


def _print_digests(title: str, digests: dict[str, str]) -> None:
    t = Table(title=title, box=BOX_TABLE, border_style=C_PRI)
    t.add_column("Algorithm", style=f"bold {C_PRI}", width=10)
    t.add_column("Digest", style=C_ACC)
    for algo, digest in digests.items():
        t.add_row(algo.upper(), digest)
    console.print(t)


def _hash_file_flow() -> None:
    raw = Prompt.ask(f"[{C_PRI}]File path[/]").strip().strip('"')
    path = Path(raw)
    if not path.is_file():
        console.print(f"[{C_CRIT}]Not a file: {path}[/]")
        return
    size = path.stat().st_size
    with console.status(f"[{C_PRI}]Hashing {path.name} ({size:,} bytes) …"):
        digests = hash_file(path)
    _print_digests(f"Digests: {path.name}", digests)


def _hash_text_flow() -> None:
    text = Prompt.ask(f"[{C_PRI}]Text to hash[/]")
    _print_digests("Digests: text input", hash_text(text))


def _verify_flow() -> None:
    raw = Prompt.ask(f"[{C_PRI}]File path[/]").strip().strip('"')
    path = Path(raw)
    if not path.is_file():
        console.print(f"[{C_CRIT}]Not a file: {path}[/]")
        return
    expected = Prompt.ask(f"[{C_PRI}]Expected checksum[/]").strip().lower()
    algo = Prompt.ask(f"[{C_PRI}]Algorithm[/]", choices=ALGOS, default="sha256")
    with console.status(f"[{C_PRI}]Verifying …"):
        actual = hash_file(path, [algo])[algo]
    match = actual == expected
    console.print(f"\nExpected : [{C_DIM}]{expected}[/]")
    console.print(f"Actual   : [{C_DIM}]{actual}[/]")
    if match:
        console.print(f"\n[bold {C_ACC}]MATCH — integrity verified.[/]")
    else:
        console.print(f"\n[bold {C_CRIT}]MISMATCH — file differs from expected![/]")


def _compare_flow() -> None:
    a = Path(Prompt.ask(f"[{C_PRI}]First file[/]").strip().strip('"'))
    b = Path(Prompt.ask(f"[{C_PRI}]Second file[/]").strip().strip('"'))
    if not (a.is_file() and b.is_file()):
        console.print(f"[{C_CRIT}]Both paths must be files.[/]")
        return
    with console.status(f"[{C_PRI}]Comparing …"):
        ha = hash_file(a, ["sha256"])["sha256"]
        hb = hash_file(b, ["sha256"])["sha256"]
    if ha == hb:
        console.print(f"[bold {C_ACC}]IDENTICAL — files share the same SHA-256.[/]")
    else:
        console.print(f"[bold {C_WARN}]DIFFERENT — files do not match.[/]")
        console.print(f"[{C_DIM}]{a.name}: {ha}[/]")
        console.print(f"[{C_DIM}]{b.name}: {hb}[/]")


def run() -> None:
    """Hash & File Integrity Toolkit menu loop."""
    header("HASH & FILE INTEGRITY")
    actions = {
        "1": _hash_file_flow,
        "2": _hash_text_flow,
        "3": _verify_flow,
        "4": _compare_flow,
    }
    while True:
        console.print(f"[bold {C_PRI}]1[/]  Hash a file (MD5/SHA1/SHA256/SHA512)")
        console.print(f"[bold {C_PRI}]2[/]  Hash text input")
        console.print(f"[bold {C_PRI}]3[/]  Verify file against a checksum")
        console.print(f"[bold {C_PRI}]4[/]  Compare two files")
        console.print(f"[bold {C_PRI}]5[/]  Back\n")
        choice = Prompt.ask(f"[{C_PRI}]>[/]", choices=["1", "2", "3", "4", "5"])
        if choice == "5":
            break
        actions[choice]()
        pause()
        console.print()
