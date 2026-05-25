from __future__ import annotations

import sys
from pathlib import PurePosixPath


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


def print_run_summary(config, plan, commit: str | None, dry_run: bool) -> None:
    print("Summary:")
    print(f"  Repo: {config.github.owner}/{config.github.repo}@{config.github.branch}")
    print(f"  Mode: {plan.mode}")
    print(f"  LeetCode submissions fetched: {plan.submissions_fetched}")
    print(
        "  Files planned: "
        f"{plan.count('create')} create(s), {plan.count('update')} update(s), {len(plan.skipped)} skip(s)"
    )
    if dry_run:
        print("  Commit: dry-run only")
    elif commit:
        print(f"  Commit: {commit}")
    else:
        print("  Commit: none")


def _group_changes_by_directory(changes):
    grouped: dict[str, list] = {}
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
