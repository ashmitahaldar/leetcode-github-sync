from __future__ import annotations

from datetime import datetime, timezone

from .config import AppConfig
from .errors import SyncError
from .github import GitHubClient
from .leetcode import LeetCodeClient
from .planner import SyncPlan, build_sync_plan


def parse_since_date(value: str | None) -> int | None:
    if not value:
        return None
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise SyncError("--since must use YYYY-MM-DD format") from exc
    return int(parsed.timestamp())


def make_commit_message(plan: SyncPlan) -> str:
    changed_solution_count = sum(1 for change in plan.changes if "/solution." in change.path)
    noun = "submission" if changed_solution_count == 1 else "submissions"
    return f"sync: add/update {changed_solution_count} accepted LeetCode {noun}"


def build_plan(
    config: AppConfig,
    leetcode: LeetCodeClient,
    github: GitHubClient,
    since: str | None = None,
) -> SyncPlan:
    submissions = leetcode.fetch_accepted_submissions(
        page_size=config.leetcode.page_size,
        since_timestamp=parse_since_date(since),
    )
    existing_files = github.list_files(config.sync.problems_root)
    return build_sync_plan(
        submissions=submissions,
        existing_files=existing_files,
        problems_root=config.sync.problems_root,
        create_notes=config.sync.create_notes,
    )
