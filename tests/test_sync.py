from dataclasses import dataclass

import pytest

from leetcode_sync.config import AppConfig, GitHubConfig, LeetCodeConfig, SyncConfig
from leetcode_sync.errors import SyncError
from leetcode_sync.sync import build_plan


@dataclass
class FakeGitHub:
    files: dict[str, str]

    def list_files(self, root: str) -> dict[str, str]:
        return self.files


class FakeLeetCode:
    def __init__(self):
        self.since_timestamp = "unset"

    def fetch_accepted_submissions(self, page_size=50, since_timestamp=None, progress=None):
        self.since_timestamp = since_timestamp
        return []


def config() -> AppConfig:
    return AppConfig(
        github=GitHubConfig(owner="octocat", repo="leetcode", branch="main"),
        sync=SyncConfig(problems_root="problems"),
        leetcode=LeetCodeConfig(page_size=50),
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

    build_plan(config(), leetcode, FakeGitHub(files=files))

    assert leetcode.since_timestamp == 13600


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
