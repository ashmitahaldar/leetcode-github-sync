from __future__ import annotations

import json

from .models import Submission


def render_solution(submission: Submission) -> str:
    return submission.code.rstrip() + "\n"


def render_metadata(submission: Submission) -> str:
    return json.dumps(_metadata_for_submission(submission), indent=2, sort_keys=True) + "\n"


def render_problem_metadata(submissions: list[Submission]) -> str:
    if not submissions:
        return "{}\n"

    first = submissions[0]
    metadata = {
        "problem_id": first.problem_id,
        "title": first.title,
        "title_slug": first.title_slug,
        "leetcode_url": f"https://leetcode.com/problems/{first.title_slug}/",
        "solutions": [_metadata_for_submission(item) for item in sorted(submissions, key=lambda item: item.language.lower())],
    }
    return json.dumps(metadata, indent=2, sort_keys=True) + "\n"


def _metadata_for_submission(submission: Submission) -> dict:
    return {
        "submission_id": submission.submission_id,
        "problem_id": submission.problem_id,
        "title": submission.title,
        "title_slug": submission.title_slug,
        "language": submission.language,
        "status": submission.status,
        "submitted_at": submission.submitted_at_iso,
        "submitted_at_unix": submission.submitted_at,
        "runtime": submission.runtime,
        "memory": submission.memory,
        "leetcode_url": submission.leetcode_url,
    }


def render_notes(submission: Submission) -> str:
    return f"# {submission.title}\n\n"
