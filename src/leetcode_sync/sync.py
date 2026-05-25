from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from .config import AppConfig
from .errors import SyncError
from .github import GitHubClient
from .leetcode import LeetCodeClient
from .metadata import incremental_cutoff
from .planner import SyncPlan, build_sync_plan, select_latest_per_language

INCREMENTAL_LOOKBACK_SECONDS = 86400


@dataclass(frozen=True)
class CutoffDecision:
    since_timestamp: int | None
    mode: str


def parse_since_date(value: str | None) -> int | None:
    if not value:
        return None
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=UTC)
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
    full_sync: bool = False,
    progress: Callable[[str], None] | None = None,
) -> SyncPlan:
    if since and full_sync:
        raise SyncError("--since cannot be combined with --full-sync")

    if progress:
        progress(f"Inspecting existing GitHub paths under {config.sync.problems_root}/...")
    existing_paths = github.list_paths(config.sync.problems_root)
    if progress:
        progress(f"Found {len(existing_paths)} existing GitHub file path(s).")

    metadata_paths = [path for path in existing_paths if path.endswith("/metadata.json")]
    if progress:
        progress(f"Fetching {len(metadata_paths)} metadata file(s) for incremental cutoff...")
    metadata_files = github.get_files(metadata_paths)

    cutoff = _select_since_timestamp(metadata_files, since, full_sync, progress)

    if progress:
        progress("Fetching accepted LeetCode submissions...")
    submissions = leetcode.fetch_accepted_submissions(
        page_size=config.leetcode.page_size,
        since_timestamp=cutoff.since_timestamp,
        progress=progress,
    )
    if progress:
        progress(f"Fetched {len(submissions)} accepted submission(s).")
        progress("Fetching existing GitHub file contents needed for planning...")
    existing_files = _fetch_candidate_existing_files(
        github=github,
        existing_paths=existing_paths,
        metadata_files=metadata_files,
        submissions=submissions,
        problems_root=config.sync.problems_root,
        create_notes=config.sync.create_notes,
    )
    if progress:
        progress(f"Fetched {len(existing_files)} existing file(s) needed for planning.")
        progress("Building sync plan...")
    plan = build_sync_plan(
        submissions=submissions,
        existing_files=existing_files,
        problems_root=config.sync.problems_root,
        create_notes=config.sync.create_notes,
    )
    plan.mode = cutoff.mode
    plan.submissions_fetched = len(submissions)
    plan.existing_files_fetched = len(existing_files)
    return plan


def _select_since_timestamp(
    existing_files: dict[str, str],
    since: str | None,
    full_sync: bool,
    progress: Callable[[str], None] | None = None,
) -> CutoffDecision:
    if since:
        timestamp = parse_since_date(since)
        if progress:
            progress(f"Using manual --since cutoff: {since}.")
        return CutoffDecision(since_timestamp=timestamp, mode="manual --since")
    if full_sync:
        if progress:
            progress("Running full sync; repository metadata cutoff is ignored.")
        return CutoffDecision(since_timestamp=None, mode="full sync")

    cutoff = incremental_cutoff(existing_files, lookback_seconds=INCREMENTAL_LOOKBACK_SECONDS)
    if cutoff is None:
        if progress:
            progress("No synced metadata found; running full backfill.")
        return CutoffDecision(since_timestamp=None, mode="full backfill")
    if progress:
        progress("Using automatic incremental cutoff from repository metadata with a one-day lookback.")
    return CutoffDecision(since_timestamp=cutoff, mode="incremental")


def _fetch_candidate_existing_files(
    github: GitHubClient,
    existing_paths: list[str],
    metadata_files: dict[str, str],
    submissions,
    problems_root: str,
    create_notes: bool,
) -> dict[str, str]:
    existing_path_set = set(existing_paths)
    candidate_content_paths = set()
    candidate_note_paths = set()
    existing_files: dict[str, str] = {}

    for submission in select_latest_per_language(submissions):
        solution_path = submission.solution_path(problems_root)
        metadata_path = submission.metadata_path(problems_root)
        notes_path = submission.notes_path(problems_root)

        if solution_path in existing_path_set:
            candidate_content_paths.add(solution_path)
        if metadata_path in metadata_files:
            existing_files[metadata_path] = metadata_files[metadata_path]
        if create_notes and notes_path in existing_path_set:
            candidate_note_paths.add(notes_path)

    for notes_path in candidate_note_paths:
        existing_files[notes_path] = ""

    paths_to_fetch = sorted(candidate_content_paths - set(existing_files))
    existing_files.update(github.get_files(paths_to_fetch))
    return existing_files
