from argparse import Namespace

import pytest

from leetcode_sync.cli import main
from leetcode_sync.commands import cmd_config_show, cmd_doctor, cmd_sync
from leetcode_sync.config import AppConfig, GitHubConfig, LeetCodeConfig, SyncConfig
from leetcode_sync.errors import SyncError
from leetcode_sync.output import print_plan
from leetcode_sync.planner import FileChange, SyncPlan
from leetcode_sync.secrets import SecretBundle


class FakeGitHub:
    def __init__(self):
        self.committed = False

    def commit_changes(self, changes, message):
        self.committed = True
        return "abc123"

    def validate_repo(self):
        return "main"


class FakeLeetCode:
    def validate_auth(self):
        return "octocat"


def config() -> AppConfig:
    return AppConfig(
        github=GitHubConfig(owner="octocat", repo="leetcode", branch="main"),
        sync=SyncConfig(problems_root="problems"),
        leetcode=LeetCodeConfig(page_size=50),
    )


def test_dry_run_does_not_commit(monkeypatch):
    github = FakeGitHub()

    def fake_build_plan(**kwargs):
        return SyncPlan()

    monkeypatch.setattr("leetcode_sync.commands.build_plan", fake_build_plan)

    result = cmd_sync(
        Namespace(dry_run=True, since=None, full_sync=False),
        config=config(),
        leetcode=FakeLeetCode(),
        github=github,
    )

    assert result == 0
    assert github.committed is False


def test_dry_run_prints_progress(monkeypatch, capsys):
    github = FakeGitHub()

    def fake_build_plan(**kwargs):
        kwargs["progress"]("fake planner progress")
        return SyncPlan()

    monkeypatch.setattr("leetcode_sync.commands.build_plan", fake_build_plan)

    result = cmd_sync(
        Namespace(dry_run=True, since=None, full_sync=False),
        config=config(),
        leetcode=FakeLeetCode(),
        github=github,
    )
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
    assert "leetcode-sync doctor" in captured.out
    assert "leetcode-sync config show" in captured.out
    assert "leetcode-sync sync --dry-run" in captured.out
    assert "leetcode-sync sync --since YYYY-MM-DD" in captured.out
    assert "leetcode-sync sync --full-sync" in captured.out


def test_help_command_prints_topic_help_without_config(capsys):
    result = main(["help", "sync"])
    captured = capsys.readouterr()

    assert result == 0
    assert "usage: leetcode-sync sync" in captured.out
    assert "--dry-run" in captured.out
    assert "--full-sync" in captured.out


def test_help_command_prints_config_help_without_config(capsys):
    result = main(["help", "config"])
    captured = capsys.readouterr()

    assert result == 0
    assert "usage: leetcode-sync config" in captured.out
    assert "show" in captured.out


def test_sync_command_rejects_since_with_full_sync():
    with pytest.raises(SyncError, match="cannot be combined"):
        cmd_sync(
            Namespace(dry_run=True, since="2026-05-01", full_sync=True),
            config=object(),
            leetcode=FakeLeetCode(),
            github=FakeGitHub(),
        )


def test_config_show_redacts_secret_values(capsys):
    secrets = SecretBundle(leetcode_session="lc-secret", csrf_token=None, github_token="gh-secret")

    result = cmd_config_show(config(), secrets)
    captured = capsys.readouterr()

    assert result == 0
    assert "octocat" in captured.out
    assert "LEETCODE_SESSION = set" in captured.out
    assert "CSRFTOKEN = missing" in captured.out
    assert "GITHUB_TOKEN = set" in captured.out
    assert "lc-secret" not in captured.out
    assert "gh-secret" not in captured.out


def test_doctor_reports_success(capsys):
    secrets = SecretBundle(leetcode_session="lc-secret", csrf_token="csrf", github_token="gh-secret")

    result = cmd_doctor(config(), secrets, FakeLeetCode(), FakeGitHub())
    captured = capsys.readouterr()

    assert result == 0
    assert "Config: ok" in captured.out
    assert "LeetCode auth: ok" in captured.out
    assert "GitHub repo: ok" in captured.out


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

    assert (
        "problems/0001-two-sum/\n  create: solution.java\n  create: metadata.json\n  create: notes.md"
        in captured.out
    )
    assert "problems/0003-longest-substring/\n  create: solution.py\n  create: metadata.json" in captured.out
