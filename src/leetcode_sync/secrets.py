from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_env_file(path: Path) -> None:
    """Load simple KEY=VALUE pairs without overriding existing environment."""
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass(frozen=True)
class SecretBundle:
    leetcode_session: str
    csrf_token: str | None
    github_token: str

    @classmethod
    def from_env(cls) -> SecretBundle:
        return cls(
            leetcode_session=os.getenv("LEETCODE_SESSION", ""),
            csrf_token=os.getenv("CSRFTOKEN") or None,
            github_token=os.getenv("GITHUB_TOKEN", ""),
        )

    def validate(self) -> list[str]:
        missing = []
        if not self.leetcode_session:
            missing.append("LEETCODE_SESSION")
        if not self.github_token:
            missing.append("GITHUB_TOKEN")
        return missing

    def values(self) -> list[str]:
        return [value for value in [self.leetcode_session, self.csrf_token, self.github_token] if value]


class Redactor:
    def __init__(self, secrets: list[str]):
        self._secrets = sorted({s for s in secrets if s}, key=len, reverse=True)

    def redact(self, message: object) -> str:
        text = str(message)
        for secret in self._secrets:
            text = text.replace(secret, "[REDACTED]")
        return text
