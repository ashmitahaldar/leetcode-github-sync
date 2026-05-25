from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .commands import cmd_config_show, cmd_doctor, cmd_help, cmd_init, cmd_status, cmd_sync
from .config import load_config
from .errors import SyncError
from .github import GitHubClient
from .http import HttpClient
from .leetcode import LeetCodeClient
from .secrets import Redactor, SecretBundle, load_env_file

DEFAULT_CONFIG = Path("leetcode-sync.toml")
DEFAULT_ENV = Path(".env")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "help":
            return cmd_help(parser, args.topic)
        if args.command == "init":
            return cmd_init()

        load_env_file(DEFAULT_ENV)
        secrets = SecretBundle.from_env()
        redactor = Redactor(secrets.values())

        config = load_config(Path(args.config))
        missing = secrets.validate()
        if args.command == "doctor":
            http = HttpClient(
                max_retries=config.sync.max_retries,
                request_delay_seconds=config.sync.request_delay_seconds,
            )
            leetcode = LeetCodeClient(secrets=secrets, http=http)
            github = GitHubClient(config=config.github, token=secrets.github_token, http=http)
            return cmd_doctor(config, secrets, leetcode, github)
        if args.command == "config" and args.config_command == "show":
            return cmd_config_show(config, secrets)
        if missing:
            raise SyncError(f"Missing required environment values: {', '.join(missing)}")

        http = HttpClient(
            max_retries=config.sync.max_retries,
            request_delay_seconds=config.sync.request_delay_seconds,
        )
        leetcode = LeetCodeClient(secrets=secrets, http=http)
        github = GitHubClient(config=config.github, token=secrets.github_token, http=http)

        if args.command == "status":
            return cmd_status(leetcode, github)
        if args.command == "sync":
            return cmd_sync(args, config, leetcode, github)

        parser.print_help()
        return 1
    except SyncError as exc:
        redactor = locals().get("redactor", Redactor([]))
        print(f"error: {redactor.redact(exc)}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="leetcode-sync",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""common commands:
  leetcode-sync init
  leetcode-sync status
  leetcode-sync doctor
  leetcode-sync config show
  leetcode-sync sync --dry-run
  leetcode-sync sync --since YYYY-MM-DD
  leetcode-sync sync --full-sync
  leetcode-sync sync

command help:
  leetcode-sync help sync
  leetcode-sync help doctor
  leetcode-sync help config
  leetcode-sync help init
  leetcode-sync help status
""",
    )
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to leetcode-sync.toml")

    subparsers = parser.add_subparsers(dest="command")

    help_parser = subparsers.add_parser("help", help="Show global or command-specific help")
    help_parser.add_argument(
        "topic",
        nargs="?",
        choices=["config", "doctor", "init", "status", "sync"],
        help="Command to explain",
    )

    init_parser = subparsers.add_parser("init", help="Create starter config and env files")
    status_parser = subparsers.add_parser("status", help="Validate configuration and remote access")
    doctor_parser = subparsers.add_parser("doctor", help="Run setup diagnostics")

    config_parser = subparsers.add_parser("config", help="Inspect non-secret configuration")
    config_subparsers = config_parser.add_subparsers(dest="config_command", required=True)
    config_subparsers.add_parser("show", help="Show config and redacted secret state")

    sync_parser = subparsers.add_parser("sync", help="Sync accepted submissions")
    sync_parser.add_argument("--dry-run", action="store_true", help="Preview changes without committing")
    sync_parser.add_argument("--since", help="Only sync submissions since YYYY-MM-DD")
    sync_parser.add_argument("--full-sync", action="store_true", help="Ignore metadata cutoff and scan all submissions")

    parser.set_defaults(
        command_parsers={
            "config": config_parser,
            "doctor": doctor_parser,
            "init": init_parser,
            "status": status_parser,
            "sync": sync_parser,
        }
    )
    return parser
