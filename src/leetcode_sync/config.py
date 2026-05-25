from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from .errors import ConfigError


@dataclass(frozen=True)
class GitHubConfig:
    owner: str
    repo: str
    branch: str = "main"


@dataclass(frozen=True)
class SyncConfig:
    problems_root: str = "problems"
    create_notes: bool = True
    request_delay_seconds: float = 0.35
    max_retries: int = 3


@dataclass(frozen=True)
class LeetCodeConfig:
    page_size: int = 50


@dataclass(frozen=True)
class AppConfig:
    github: GitHubConfig
    sync: SyncConfig
    leetcode: LeetCodeConfig


def load_config(path: Path) -> AppConfig:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Invalid TOML in {path}: {exc}") from exc

    github_data = data.get("github", {})
    sync_data = data.get("sync", {})
    leetcode_data = data.get("leetcode", {})

    github = GitHubConfig(
        owner=str(github_data.get("owner", "")).strip(),
        repo=str(github_data.get("repo", "")).strip(),
        branch=str(github_data.get("branch", "main")).strip() or "main",
    )
    sync = SyncConfig(
        problems_root=str(sync_data.get("problems_root", "problems")).strip("/") or "problems",
        create_notes=bool(sync_data.get("create_notes", True)),
        request_delay_seconds=float(sync_data.get("request_delay_seconds", 0.35)),
        max_retries=int(sync_data.get("max_retries", 3)),
    )
    leetcode = LeetCodeConfig(page_size=int(leetcode_data.get("page_size", 50)))
    config = AppConfig(github=github, sync=sync, leetcode=leetcode)
    validate_config(config)
    return config


def validate_config(config: AppConfig) -> None:
    if not config.github.owner or config.github.owner == "your-github-username":
        raise ConfigError("Set github.owner in leetcode-sync.toml")
    if not config.github.repo or config.github.repo == "your-target-repo":
        raise ConfigError("Set github.repo in leetcode-sync.toml")
    if not config.github.branch:
        raise ConfigError("Set github.branch in leetcode-sync.toml")
    if config.sync.request_delay_seconds < 0:
        raise ConfigError("sync.request_delay_seconds must be >= 0")
    if config.sync.max_retries < 0:
        raise ConfigError("sync.max_retries must be >= 0")
    if config.leetcode.page_size <= 0:
        raise ConfigError("leetcode.page_size must be > 0")
