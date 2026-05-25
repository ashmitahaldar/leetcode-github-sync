from __future__ import annotations

import argparse
from pathlib import Path

from .errors import SyncError
from .github import GitHubClient
from .leetcode import LeetCodeClient
from .output import log_progress, print_plan, print_run_summary
from .secrets import SecretBundle
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


def cmd_doctor(config, secrets: SecretBundle, leetcode: LeetCodeClient, github: GitHubClient) -> int:
    ok = True
    print("Config: ok")
    print(f"Target repo: {config.github.owner}/{config.github.repo}@{config.github.branch}")

    missing = secrets.validate()
    if missing:
        ok = False
        print("Secrets: missing " + ", ".join(missing))
    else:
        print("Secrets: required values are set")
    print(f"Optional CSRFTOKEN: {'set' if secrets.csrf_token else 'not set'}")

    if secrets.leetcode_session:
        try:
            username = leetcode.validate_auth()
            print(f"LeetCode auth: ok, signed in as {username}")
        except SyncError as exc:
            ok = False
            print(f"LeetCode auth: failed - {exc}")
    else:
        print("LeetCode auth: skipped because LEETCODE_SESSION is missing")

    if secrets.github_token:
        try:
            default_branch = github.validate_repo()
            print(f"GitHub repo: ok, default branch is {default_branch}")
        except SyncError as exc:
            ok = False
            print(f"GitHub repo: failed - {exc}")
    else:
        print("GitHub repo: skipped because GITHUB_TOKEN is missing")

    return 0 if ok else 1


def cmd_config_show(config, secrets: SecretBundle) -> int:
    print("[github]")
    print(f"owner = {config.github.owner}")
    print(f"repo = {config.github.repo}")
    print(f"branch = {config.github.branch}")
    print()
    print("[sync]")
    print(f"problems_root = {config.sync.problems_root}")
    print(f"create_notes = {config.sync.create_notes}")
    print(f"request_delay_seconds = {config.sync.request_delay_seconds}")
    print(f"max_retries = {config.sync.max_retries}")
    print()
    print("[leetcode]")
    print(f"page_size = {config.leetcode.page_size}")
    print()
    print("[env]")
    print(f"LEETCODE_SESSION = {_secret_state(secrets.leetcode_session)}")
    print(f"CSRFTOKEN = {_secret_state(secrets.csrf_token)}")
    print(f"GITHUB_TOKEN = {_secret_state(secrets.github_token)}")
    return 0


def cmd_sync(args: argparse.Namespace, config, leetcode: LeetCodeClient, github: GitHubClient) -> int:
    if args.since and args.full_sync:
        raise SyncError("--since cannot be combined with --full-sync")

    log_progress("Starting dry run..." if args.dry_run else "Starting sync...")
    plan = build_plan(
        config=config,
        leetcode=leetcode,
        github=github,
        since=args.since,
        full_sync=args.full_sync,
        progress=log_progress,
    )
    log_progress("Sync plan ready.")
    print_plan(plan)

    if args.dry_run:
        log_progress("Dry run finished without writing to GitHub.")
        print("Dry run complete; no GitHub changes were written.")
        print_run_summary(config, plan, commit=None, dry_run=True)
        return 0

    if not plan.has_changes:
        log_progress("No GitHub commit needed.")
        print("No changes to commit.")
        print_run_summary(config, plan, commit=None, dry_run=False)
        return 0

    message = make_commit_message(plan)
    log_progress(f"Creating GitHub commit with {len(plan.changes)} file change(s)...")
    sha = github.commit_changes(plan.changes, message)
    log_progress("GitHub commit created.")
    print(f"Committed {len(plan.changes)} file change(s): {sha}")
    print_run_summary(config, plan, commit=sha, dry_run=False)
    return 0


def _secret_state(value: str | None) -> str:
    return "set" if value else "missing"
