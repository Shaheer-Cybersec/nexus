"""Task Nexus: a small persistent priority task manager.

Tasks live as JSON under the user data directory so they survive restarts.
"""

from __future__ import annotations

import json
from datetime import datetime

from rich.prompt import IntPrompt, Prompt
from rich.table import Table

from ..paths import TASKS_FILE, ensure_dirs
from ..theme import BOX_TABLE, C_ACC, C_CRIT, C_DIM, C_PRI, C_WARN
from ..ui import console, header

PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
PRIORITY_COLOR = {"high": C_CRIT, "medium": C_WARN, "low": C_ACC}


def load_tasks() -> list[dict]:
    """Load the task list, returning an empty list if absent/corrupt."""
    if TASKS_FILE.exists():
        try:
            return json.loads(TASKS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
    return []


def save_tasks(tasks: list[dict]) -> None:
    """Persist the task list to disk."""
    ensure_dirs()
    TASKS_FILE.write_text(json.dumps(tasks, indent=2), encoding="utf-8")


def _sorted(tasks: list[dict]) -> list[dict]:
    """Sort: incomplete first, then by priority, then by due date."""
    return sorted(
        tasks,
        key=lambda t: (
            t.get("done", False),
            PRIORITY_RANK.get(t.get("priority", "medium"), 1),
            t.get("due") or "9999-99-99",
        ),
    )


def _render(tasks: list[dict]) -> None:
    if not tasks:
        console.print(f"[{C_DIM}]No tasks yet.[/]\n")
        return
    t = Table(box=BOX_TABLE, border_style=C_PRI)
    t.add_column("#", style=f"bold {C_PRI}", width=4)
    t.add_column("Task", style="white")
    t.add_column("Priority", width=10)
    t.add_column("Due", width=12)
    t.add_column("Status", width=10)

    today = datetime.now().strftime("%Y-%m-%d")
    for i, task in enumerate(tasks, 1):
        done = task.get("done", False)
        prio = task.get("priority", "medium")
        pc = PRIORITY_COLOR.get(prio, C_ACC)
        style = "dim strike" if done else "white"
        due = task.get("due") or "—"
        due_disp = (f"[{C_CRIT}]{due}[/]" if (not done and due != "—" and due < today)
                    else due)
        t.add_row(
            str(i),
            f"[{style}]{task['title']}[/]",
            f"[bold {pc}]{prio.upper()}[/]",
            due_disp,
            f"[{C_ACC}]DONE[/]" if done else f"[{C_WARN}]PENDING[/]",
        )
    console.print(t)


def run() -> None:
    """Task Nexus menu loop."""
    header("TASK NEXUS")
    while True:
        tasks = _sorted(load_tasks())
        _render(tasks)

        console.print(
            f"[bold {C_PRI}]1[/] Add   [bold {C_PRI}]2[/] Done   "
            f"[bold {C_PRI}]3[/] Delete   [bold {C_PRI}]4[/] Clear Completed   "
            f"[bold {C_PRI}]5[/] Back\n"
        )
        choice = Prompt.ask(f"[{C_PRI}]>[/]", choices=["1", "2", "3", "4", "5"])

        if choice == "5":
            break

        if choice == "1":
            title = Prompt.ask(f"[{C_PRI}]Title[/]").strip()
            if not title:
                continue
            priority = Prompt.ask(f"[{C_PRI}]Priority[/]",
                                  choices=["high", "medium", "low"], default="medium")
            due = Prompt.ask(f"[{C_PRI}]Due date (YYYY-MM-DD, blank = none)[/]",
                             default="").strip()
            tasks.append({
                "title": title, "priority": priority,
                "due": due or None, "done": False,
                "created": datetime.now().isoformat(timespec="seconds"),
            })
            save_tasks(tasks)
            console.print(f"[{C_ACC}]Added[/]")

        elif choice in ("2", "3"):
            if not tasks:
                console.print(f"[{C_WARN}]Nothing to do.[/]")
                continue
            n = IntPrompt.ask(f"[{C_PRI}]Task #[/]", default=1)
            if 1 <= n <= len(tasks):
                if choice == "2":
                    tasks[n - 1]["done"] = True
                    console.print(f"[{C_ACC}]Marked done[/]")
                else:
                    removed = tasks.pop(n - 1)
                    console.print(f"[{C_ACC}]Deleted: {removed['title']}[/]")
                save_tasks(tasks)

        elif choice == "4":
            tasks = [t for t in tasks if not t.get("done", False)]
            save_tasks(tasks)
            console.print(f"[{C_ACC}]Cleared completed tasks[/]")

        console.print()
