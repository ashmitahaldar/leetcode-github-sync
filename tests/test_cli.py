from argparse import Namespace

from leetcode_sync.cli import main
from leetcode_sync.commands import cmd_sync
from leetcode_sync.output import print_plan
from leetcode_sync.planner import FileChange, SyncPlan


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

    monkeypatch.setattr("leetcode_sync.commands.build_plan", fake_build_plan)

    result = cmd_sync(Namespace(dry_run=True, since=None), config=object(), leetcode=FakeLeetCode(), github=github)

    assert result == 0
    assert github.committed is False


def test_dry_run_prints_progress(monkeypatch, capsys):
    github = FakeGitHub()

    def fake_build_plan(**kwargs):
        kwargs["progress"]("fake planner progress")
        return SyncPlan()

    monkeypatch.setattr("leetcode_sync.commands.build_plan", fake_build_plan)

    result = cmd_sync(Namespace(dry_run=True, since=None), config=object(), leetcode=FakeLeetCode(), github=github)
    captured = capsys.readouterr()

    assert result == 0
    assert "[leetcode-sync] Starting dry run..." in captured.err
    assert "[leetcode-sync] fake planner progress" in captured.err
    assert "Dry run complete" in captured.out


def test_help_command_prints_global_help_without_config(capsys):
    result = main(["help"])
    captured = capsys.readouterr()

    assert result == 0
    assert "usage: leetcode-sync" in captured.out
    assert "sync" in captured.out
    assert "leetcode-sync sync --dry-run" in captured.out
    assert "leetcode-sync sync --since YYYY-MM-DD" in captured.out


def test_help_command_prints_topic_help_without_config(capsys):
    result = main(["help", "sync"])
    captured = capsys.readouterr()

    assert result == 0
    assert "usage: leetcode-sync sync" in captured.out
    assert "--dry-run" in captured.out


def test_print_plan_groups_changes_by_problem(capsys):
    plan = SyncPlan(
        changes=[
            FileChange("problems/0001-two-sum/solution.java", "code", "create"),
            FileChange("problems/0003-longest-substring/solution.py", "code", "create"),
            FileChange("problems/0001-two-sum/notes.md", "# Notes", "create"),
            FileChange("problems/0003-longest-substring/metadata.json", "{}", "create"),
            FileChange("problems/0001-two-sum/metadata.json", "{}", "create"),
        ]
    )

    print_plan(plan)
    captured = capsys.readouterr()

    assert "problems/0001-two-sum/\n  create: solution.java\n  create: metadata.json\n  create: notes.md" in captured.out
    assert "problems/0003-longest-substring/\n  create: solution.py\n  create: metadata.json" in captured.out
