from argparse import Namespace

from leetcode_sync.cli import cmd_sync
from leetcode_sync.planner import SyncPlan


class FakeGitHub:
    def __init__(self):
        self.committed = False

    def commit_changes(self, changes, message):
        self.committed = True
        return "abc123"


class FakeLeetCode:
    pass


def test_dry_run_does_not_commit(monkeypatch):
    github = FakeGitHub()

    def fake_build_plan(**kwargs):
        return SyncPlan()

    monkeypatch.setattr("leetcode_sync.cli.build_plan", fake_build_plan)

    result = cmd_sync(Namespace(dry_run=True, since=None), config=object(), leetcode=FakeLeetCode(), github=github)

    assert result == 0
    assert github.committed is False
