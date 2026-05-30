#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convenience launcher for NEXUS.

This thin wrapper lets you run the tool with ``python nexus.py`` without
installing it. It checks for the required third-party packages and offers
to install them, then hands off to the ``nexus`` package.

For the canonical entry points use either::

    python -m nexus      # run the package directly
    nexus                # if installed via `pip install .`
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys

REQUIRED = ["rich", "requests", "psutil"]


def _ensure_deps() -> None:
    """Install any missing third-party dependencies after confirmation."""
    missing = [pkg for pkg in REQUIRED if importlib.util.find_spec(pkg) is None]
    if not missing:
        return
    print(f"[*] NEXUS needs: {', '.join(missing)}")
    answer = input("    Install them now with pip? [Y/n] ").strip().lower()
    if answer in ("", "y", "yes"):
        subprocess.run([sys.executable, "-m", "pip", "install", *missing], check=True)
        print("[*] Dependencies installed.\n")
    else:
        print("[!] Cannot continue without dependencies. Exiting.")
        sys.exit(1)


def main() -> int:
    _ensure_deps()
    from nexus.__main__ import main as nexus_main
    return nexus_main()


if __name__ == "__main__":
    sys.exit(main())
