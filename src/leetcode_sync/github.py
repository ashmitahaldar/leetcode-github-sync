from __future__ import annotations

from dataclasses import dataclass
import base64
from typing import Any
from urllib.parse import quote

from .config import GitHubConfig
from .errors import RemoteApiError
from .http import HttpClient
from .planner import FileChange


@dataclass(frozen=True)
class BranchState:
    sha: str
    tree_sha: str


class GitHubClient:
    api_root = "https://api.github.com"

    def __init__(self, config: GitHubConfig, token: str, http: HttpClient):
        self.config = config
        self.token = token
        self.http = http

    def validate_repo(self) -> str:
        data = self._request("GET", f"/repos/{self.config.owner}/{self.config.repo}")
        default_branch = str(data.get("default_branch") or "")
        return default_branch

    def list_files(self, root: str) -> dict[str, str]:
        branch = self._branch_state()
        tree = self._request(
            "GET",
            f"/repos/{self.config.owner}/{self.config.repo}/git/trees/{branch.tree_sha}?recursive=1",
        )
        files: dict[str, str] = {}
        for item in tree.get("tree", []):
            if item.get("type") != "blob":
                continue
            path = str(item.get("path", ""))
            if not path.startswith(root.rstrip("/") + "/"):
                continue
            files[path] = self.get_file(path)
        return files

    def get_file(self, path: str) -> str:
        encoded_path = quote(path, safe="/")
        data = self._request(
            "GET",
            f"/repos/{self.config.owner}/{self.config.repo}/contents/{encoded_path}?ref={self.config.branch}",
        )
        content = str(data.get("content", ""))
        encoding = data.get("encoding")
        if encoding != "base64":
            raise RemoteApiError(f"Unexpected encoding for GitHub file {path}: {encoding}")
        return base64.b64decode(content).decode("utf-8")

    def commit_changes(self, changes: list[FileChange], message: str) -> str:
        if not changes:
            raise RemoteApiError("No changes to commit")

        branch = self._branch_state()
        tree_items = [
            {
                "path": change.path,
                "mode": "100644",
                "type": "blob",
                "content": change.content,
            }
            for change in changes
        ]
        tree = self._request(
            "POST",
            f"/repos/{self.config.owner}/{self.config.repo}/git/trees",
            {"base_tree": branch.tree_sha, "tree": tree_items},
        )
        commit = self._request(
            "POST",
            f"/repos/{self.config.owner}/{self.config.repo}/git/commits",
            {"message": message, "tree": tree["sha"], "parents": [branch.sha]},
        )
        self._request(
            "PATCH",
            f"/repos/{self.config.owner}/{self.config.repo}/git/refs/heads/{self.config.branch}",
            {"sha": commit["sha"], "force": False},
        )
        return str(commit["sha"])

    def _branch_state(self) -> BranchState:
        ref = self._request(
            "GET",
            f"/repos/{self.config.owner}/{self.config.repo}/git/ref/heads/{self.config.branch}",
        )
        commit_sha = ref.get("object", {}).get("sha")
        if not commit_sha:
            raise RemoteApiError(f"GitHub branch not found: {self.config.branch}")
        commit = self._request("GET", f"/repos/{self.config.owner}/{self.config.repo}/git/commits/{commit_sha}")
        tree_sha = commit.get("tree", {}).get("sha")
        if not tree_sha:
            raise RemoteApiError(f"GitHub branch has no tree: {self.config.branch}")
        return BranchState(sha=str(commit_sha), tree_sha=str(tree_sha))

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.http.request_json(
            method,
            f"{self.api_root}{path}",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "leetcode-github-sync",
            },
            body=body,
        ).data
