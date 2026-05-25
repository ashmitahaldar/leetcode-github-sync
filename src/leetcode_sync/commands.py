from __future__ import annotations

import argparse
from pathlib import Path

from .github import GitHubClient
from .leetcode import LeetCodeClient
from .output import log_progress, print_plan
from .sync import build_plan, make_commit_message
from .templates import CONFIG_TEMPLATE, ENV_EXAMPLE_TEMPLATE, GITIGNORE_ENTRIES, README_TEMPLATE


def cmd_help(parser: argparse.ArgumentParser, topic: str | None) -> int:
    if topic:
        parser.get_default("command_parsers")[topic].print_help()
    else:
        parser.print_help()
    return 0


def cmd_init() -> int:
    created = []
    starter_files = {
        "leetcode-sync.toml": CONFIG_TEMPLATE,
        ".env.example": ENV_EXAMPLE_TEMPLATE,
        "README.md": README_TEMPLATE,
    }
    for filename, content in starter_files.items():
        target = Path(filename)
        if not target.exists():
            target.write_text(content, encoding="utf-8")
            created.append(filename)

    gitignore = Path(".gitignore")
    existing_entries = set(gitignore.read_text(encoding="utf-8").splitlines()) if gitignore.exists() else set()
    missing_entries = [entry for entry in GITIGNORE_ENTRIES if entry not in existing_entries]
    if missing_entries:
        with gitignore.open("a", encoding="utf-8") as handle:
            if gitignore.exists() and gitignore.stat().st_size > 0:
                handle.write("\n")
            handle.write("\n".join(missing_entries) + "\n")
        created.append(".gitignore entries")

    if not created:
        print("No files created; starter files already exist.")
    else:
        print("Created: " + ", ".join(created))
    return 0


def cmd_status(leetcode: LeetCodeClient, github: GitHubClient) -> int:
    username = leetcode.validate_auth()
    default_branch = github.validate_repo()
    print(f"LeetCode auth: signed in as {username}")
    print(f"GitHub repo: accessible, default branch is {default_branch}")
    return 0


def cmd_sync(args: argparse.Namespace, config, leetcode: LeetCodeClient, github: GitHubClient) -> int:
    log_progress("Starting dry run..." if args.dry_run else "Starting sync...")
    plan = build_plan(config=config, leetcode=leetcode, github=github, since=args.since, progress=log_progress)
    log_progress("Sync plan ready.")
    print_plan(plan)

    if args.dry_run:
        log_progress("Dry run finished without writing to GitHub.")
        print("Dry run complete; no GitHub changes were written.")
        return 0

    if not plan.has_changes:
        log_progress("No GitHub commit needed.")
        print("No changes to commit.")
        return 0

    message = make_commit_message(plan)
    log_progress(f"Creating GitHub commit with {len(plan.changes)} file change(s)...")
    sha = github.commit_changes(plan.changes, message)
    log_progress("GitHub commit created.")
    print(f"Committed {len(plan.changes)} file change(s): {sha}")
    return 0
