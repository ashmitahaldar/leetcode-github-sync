import json

from leetcode_sync.models import Submission
from leetcode_sync.planner import build_sync_plan, select_latest_per_language
from leetcode_sync.render import render_problem_metadata, render_solution


def submission(
    submission_id: str = "1",
    problem_id: int = 1,
    language: str = "Python3",
    code: str = "class Solution:\n    pass",
    submitted_at: int = 100,
    status: str = "Accepted",
) -> Submission:
    return Submission(
        submission_id=submission_id,
        problem_id=problem_id,
        title="Two Sum",
        title_slug="two-sum",
        language=language,
        code=code,
        status=status,
        submitted_at=submitted_at,
        runtime="42 ms",
        memory="16 MB",
    )


def test_select_latest_accepted_per_language():
    old = submission(submission_id="old", submitted_at=100)
    new = submission(submission_id="new", submitted_at=200)
    failed = submission(submission_id="failed", submitted_at=300, status="Wrong Answer")
    java = submission(submission_id="java", language="Java", submitted_at=150)

    selected = select_latest_per_language([old, new, failed, java])

    assert [item.submission_id for item in selected] == ["java", "new"]


def test_plan_creates_solution_metadata_and_notes():
    plan = build_sync_plan([submission()], existing_files={}, problems_root="problems")

    paths = {change.path for change in plan.changes}

    assert "problems/0001-two-sum/solution.py" in paths
    assert "problems/0001-two-sum/metadata.json" in paths
    assert "problems/0001-two-sum/notes.md" in paths


def test_idempotent_when_generated_files_match():
    item = submission()
    existing = {
        item.solution_path("problems"): render_solution(item),
        item.metadata_path("problems"): render_problem_metadata([item]),
        item.notes_path("problems"): "# My notes\n",
    }

    plan = build_sync_plan([item], existing_files=existing, problems_root="problems")

    assert plan.changes == []


def test_notes_are_never_overwritten():
    item = submission()
    existing = {
        item.notes_path("problems"): "# User edited notes\n",
    }

    plan = build_sync_plan([item], existing_files=existing, problems_root="problems")

    assert all(change.path != item.notes_path("problems") for change in plan.changes)


def test_generated_solution_updates_for_newer_submission():
    old = submission(submission_id="old", submitted_at=100, code="old code")
    new = submission(submission_id="new", submitted_at=200, code="new code")
    existing = {
        old.solution_path("problems"): render_solution(old),
        old.metadata_path("problems"): render_problem_metadata([old]),
    }

    plan = build_sync_plan([new], existing_files=existing, problems_root="problems")

    solution_changes = [change for change in plan.changes if change.path.endswith("solution.py")]
    assert len(solution_changes) == 1
    assert solution_changes[0].content == "new code\n"


def test_metadata_json_contains_expected_fields():
    item = submission()
    plan = build_sync_plan([item], existing_files={}, problems_root="problems")
    metadata_change = next(change for change in plan.changes if change.path.endswith("metadata.json"))

    data = json.loads(metadata_change.content)

    assert data["problem_id"] == 1
    assert data["leetcode_url"].endswith("/two-sum/")
    assert data["solutions"][0]["submission_id"] == "1"
    assert data["solutions"][0]["leetcode_url"].endswith("/two-sum/submissions/1/")


def test_metadata_json_aggregates_multiple_languages():
    python = submission(submission_id="py", language="Python3", submitted_at=100)
    java = submission(submission_id="java", language="Java", submitted_at=200)

    plan = build_sync_plan([python, java], existing_files={}, problems_root="problems")
    metadata_changes = [change for change in plan.changes if change.path.endswith("metadata.json")]

    assert len(metadata_changes) == 1
    data = json.loads(metadata_changes[0].content)
    assert {solution["submission_id"] for solution in data["solutions"]} == {"py", "java"}
