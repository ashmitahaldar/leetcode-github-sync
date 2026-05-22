from __future__ import annotations

from dataclasses import dataclass, field
import json

from .models import Submission
from .render import render_notes, render_problem_metadata, render_solution


@dataclass(frozen=True)
class FileChange:
    path: str
    content: str
    action: str
    generated: bool = True


@dataclass
class SyncPlan:
    changes: list[FileChange] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.changes)

    def count(self, action: str) -> int:
        return sum(1 for change in self.changes if change.action == action)


def select_latest_per_language(submissions: list[Submission]) -> list[Submission]:
    selected: dict[tuple[int, str], Submission] = {}
    for submission in submissions:
        if submission.status.lower() != "accepted":
            continue
        key = submission.identity_key()
        current = selected.get(key)
        if current is None or submission.submitted_at > current.submitted_at:
            selected[key] = submission
    return sorted(selected.values(), key=lambda item: (item.problem_id, item.language.lower()))


def build_sync_plan(
    submissions: list[Submission],
    existing_files: dict[str, str],
    problems_root: str,
    create_notes: bool = True,
) -> SyncPlan:
    plan = SyncPlan()
    selected = select_latest_per_language(submissions)
    grouped: dict[int, list[Submission]] = {}
    for submission in selected:
        grouped.setdefault(submission.problem_id, []).append(submission)

    for submission in selected:
        solution_path = submission.solution_path(problems_root)
        metadata_path = submission.metadata_path(problems_root)
        notes_path = submission.notes_path(problems_root)

        existing_metadata = _parse_metadata(existing_files.get(metadata_path))
        existing_solution_metadata = _metadata_for_language(existing_metadata, submission.language)
        existing_submission_id = str(existing_solution_metadata.get("submission_id", "")) if existing_solution_metadata else ""
        existing_timestamp = (
            int(existing_solution_metadata.get("submitted_at_unix", 0)) if existing_solution_metadata else 0
        )

        if existing_submission_id == submission.submission_id:
            plan.skipped.append(solution_path)
        elif existing_timestamp > submission.submitted_at:
            plan.skipped.append(solution_path)
            plan.warnings.append(
                f"Skipped {solution_path}: repository metadata is newer than LeetCode submission {submission.submission_id}"
            )
        else:
            _add_if_changed(plan, existing_files, solution_path, render_solution(submission), generated=True)

        if create_notes and notes_path not in existing_files:
            plan.changes.append(FileChange(path=notes_path, content=render_notes(submission), action="create", generated=False))
        elif create_notes:
            plan.skipped.append(notes_path)

    for problem_submissions in grouped.values():
        metadata_path = problem_submissions[0].metadata_path(problems_root)
        _add_if_changed(
            plan,
            existing_files,
            metadata_path,
            render_problem_metadata(problem_submissions),
            generated=True,
        )

    return plan


def _add_if_changed(
    plan: SyncPlan,
    existing_files: dict[str, str],
    path: str,
    content: str,
    generated: bool,
) -> None:
    if path not in existing_files:
        plan.changes.append(FileChange(path=path, content=content, action="create", generated=generated))
    elif existing_files[path] != content:
        plan.changes.append(FileChange(path=path, content=content, action="update", generated=generated))
    else:
        plan.skipped.append(path)


def _parse_metadata(content: str | None) -> dict:
    if not content:
        return {}
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _metadata_for_language(metadata: dict, language: str) -> dict:
    solutions = metadata.get("solutions")
    if isinstance(solutions, list):
        for solution in solutions:
            if not isinstance(solution, dict):
                continue
            if str(solution.get("language", "")).lower() == language.lower():
                return solution
        return {}

    if str(metadata.get("language", "")).lower() == language.lower():
        return metadata
    return {}
