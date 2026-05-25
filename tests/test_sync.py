from dataclasses import dataclass, field

import pytest

from leetcode_sync.config import AppConfig, GitHubConfig, LeetCodeConfig, SyncConfig
from leetcode_sync.errors import SyncError
from leetcode_sync.models import Submission
from leetcode_sync.sync import build_plan


@dataclass
class FakeGitHub:
    files: dict[str, str]
    fetched_paths: list[str] = field(default_factory=list)

    def list_paths(self, root: str) -> list[str]:
        return sorted(path for path in self.files if path.startswith(root.rstrip("/") + "/"))

    def get_files(self, paths: list[str]) -> dict[str, str]:
        self.fetched_paths.extend(paths)
        return {path: self.files[path] for path in paths}


class FakeLeetCode:
    def __init__(self, submissions=None):
        self.since_timestamp = "unset"
        self.submissions = submissions or []

    def fetch_accepted_submissions(self, page_size=50, since_timestamp=None, progress=None):
        self.since_timestamp = since_timestamp
        return self.submissions


def config() -> AppConfig:
    return AppConfig(
        github=GitHubConfig(owner="octocat", repo="leetcode", branch="main"),
        sync=SyncConfig(problems_root="problems"),
        leetcode=LeetCodeConfig(page_size=50),
    )


def submission() -> Submission:
    return Submission(
        submission_id="new",
        problem_id=1,
        title="Two Sum",
        title_slug="two-sum",
        language="Python3",
        code="class Solution:\n    pass",
        status="Accepted",
        submitted_at=100001,
        runtime="42 ms",
        memory="16 MB",
    )


def test_build_plan_uses_full_backfill_when_no_metadata():
    leetcode = FakeLeetCode()

    build_plan(config(), leetcode, FakeGitHub(files={}))

    assert leetcode.since_timestamp is None


def test_build_plan_uses_incremental_cutoff_from_metadata():
    leetcode = FakeLeetCode()
    files = {
        "problems/0001-two-sum/metadata.json": '{"solutions": [{"submitted_at_unix": 100000}]}',
    }

    plan = build_plan(config(), leetcode, FakeGitHub(files=files))

    assert leetcode.since_timestamp == 13600
    assert plan.mode == "incremental"


def test_build_plan_since_overrides_metadata_cutoff():
    leetcode = FakeLeetCode()
    files = {
        "problems/0001-two-sum/metadata.json": '{"solutions": [{"submitted_at_unix": 100000}]}',
    }

    build_plan(config(), leetcode, FakeGitHub(files=files), since="2026-05-01")

    assert leetcode.since_timestamp == 1777593600


def test_build_plan_full_sync_ignores_metadata_cutoff():
    leetcode = FakeLeetCode()
    files = {
        "problems/0001-two-sum/metadata.json": '{"solutions": [{"submitted_at_unix": 100000}]}',
    }

    build_plan(config(), leetcode, FakeGitHub(files=files), full_sync=True)

    assert leetcode.since_timestamp is None


def test_build_plan_rejects_since_with_full_sync():
    with pytest.raises(SyncError, match="cannot be combined"):
        build_plan(config(), FakeLeetCode(), FakeGitHub(files={}), since="2026-05-01", full_sync=True)


def test_build_plan_fetches_only_candidate_existing_file_contents():
    files = {
        "problems/0001-two-sum/metadata.json": '{"solutions": [{"submitted_at_unix": 100000}]}',
        "problems/0001-two-sum/solution.py": "old code\n",
        "problems/0001-two-sum/notes.md": "# notes\n",
        "problems/9999-unrelated/metadata.json": '{"solutions": [{"submitted_at_unix": 1}]}',
        "problems/9999-unrelated/solution.py": "unrelated\n",
    }
    github = FakeGitHub(files=files)

    build_plan(config(), FakeLeetCode(submissions=[submission()]), github)

    assert "problems/0001-two-sum/metadata.json" in github.fetched_paths
    assert "problems/9999-unrelated/metadata.json" in github.fetched_paths
    assert "problems/0001-two-sum/solution.py" in github.fetched_paths
    assert "problems/0001-two-sum/notes.md" not in github.fetched_paths
    assert "problems/9999-unrelated/solution.py" not in github.fetched_paths
