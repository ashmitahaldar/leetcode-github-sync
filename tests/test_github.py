import pytest

from leetcode_sync.config import GitHubConfig
from leetcode_sync.errors import ApiResponseError, RemoteApiError
from leetcode_sync.github import GitHubClient


class FakeHttp:
    def __init__(self, responses):
        self.responses = responses

    def request_json(self, method, url, headers=None, body=None):
        path = url.replace("https://api.github.com", "")
        response = self.responses[(method, path)]
        if isinstance(response, Exception):
            raise response
        return type("Response", (), {"data": response})()


def client(responses):
    return GitHubClient(
        config=GitHubConfig(owner="octocat", repo="leetcode", branch="main"),
        token="token",
        http=FakeHttp(responses),
    )


def valid_branch_responses():
    return {
        ("GET", "/repos/octocat/leetcode"): {
            "default_branch": "main",
            "permissions": {"push": True},
        },
        ("GET", "/repos/octocat/leetcode/git/ref/heads/main"): {
            "object": {"sha": "commit-sha"},
        },
        ("GET", "/repos/octocat/leetcode/git/commits/commit-sha"): {
            "tree": {"sha": "tree-sha"},
        },
    }


def test_validate_repo_checks_branch_and_returns_default_branch():
    assert client(valid_branch_responses()).validate_repo() == "main"


def test_validate_repo_reports_inaccessible_repository():
    responses = {
        ("GET", "/repos/octocat/leetcode"): ApiResponseError("not found", status=404),
    }

    with pytest.raises(RemoteApiError, match="not accessible"):
        client(responses).validate_repo()


def test_validate_repo_reports_empty_repository_without_default_branch():
    responses = {
        ("GET", "/repos/octocat/leetcode"): {"default_branch": ""},
    }

    with pytest.raises(RemoteApiError, match="appears to be empty"):
        client(responses).validate_repo()


def test_validate_repo_reports_read_only_token_permissions():
    responses = {
        ("GET", "/repos/octocat/leetcode"): {
            "default_branch": "main",
            "permissions": {"push": False},
        },
    }

    with pytest.raises(RemoteApiError, match="cannot write"):
        client(responses).validate_repo()


def test_validate_repo_reports_missing_configured_branch():
    responses = {
        ("GET", "/repos/octocat/leetcode"): {
            "default_branch": "main",
            "permissions": {"push": True},
        },
        ("GET", "/repos/octocat/leetcode/git/ref/heads/main"): ApiResponseError("missing", status=404),
    }

    with pytest.raises(RemoteApiError, match="branch 'main' was not found"):
        client(responses).validate_repo()


def test_validate_repo_reports_empty_git_repository():
    responses = {
        ("GET", "/repos/octocat/leetcode"): {
            "default_branch": "main",
            "permissions": {"push": True},
        },
        ("GET", "/repos/octocat/leetcode/git/ref/heads/main"): ApiResponseError("empty", status=409),
    }

    with pytest.raises(RemoteApiError, match="repository octocat/leetcode is empty"):
        client(responses).validate_repo()
