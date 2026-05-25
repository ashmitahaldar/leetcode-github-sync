from __future__ import annotations

from pathlib import PurePosixPath
import sys


def log_progress(message: str) -> None:
    print(f"[leetcode-sync] {message}", file=sys.stderr, flush=True)


def print_plan(plan) -> None:
    creates = plan.count("create")
    updates = plan.count("update")
    print(f"Planned changes: {creates} create(s), {updates} update(s), {len(plan.skipped)} skip(s)")
    for warning in plan.warnings:
        print(f"warning: {warning}")
    for directory, changes in _group_changes_by_directory(plan.changes).items():
        print(f"{directory}/")
        for change in changes:
            filename = PurePosixPath(change.path).name
            print(f"  {change.action}: {filename}")


def _group_changes_by_directory(changes):
    grouped = {}
    for change in changes:
        path = PurePosixPath(change.path)
        directory = str(path.parent) if str(path.parent) != "." else "(root)"
        grouped.setdefault(directory, []).append(change)

    return {
        directory: sorted(items, key=lambda change: _file_display_order(PurePosixPath(change.path).name))
        for directory, items in sorted(grouped.items())
    }


def _file_display_order(filename: str) -> tuple[int, str]:
    if filename.startswith("solution."):
        return (0, filename)
    if filename == "metadata.json":
        return (1, filename)
    if filename == "notes.md":
        return (2, filename)
    return (3, filename)
