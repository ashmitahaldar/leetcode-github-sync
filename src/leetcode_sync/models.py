from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import PurePosixPath
import re


LANGUAGE_EXTENSIONS = {
    "python": "py",
    "python3": "py",
    "java": "java",
    "c++": "cpp",
    "cpp": "cpp",
    "c": "c",
    "c#": "cs",
    "csharp": "cs",
    "javascript": "js",
    "typescript": "ts",
    "go": "go",
    "golang": "go",
    "ruby": "rb",
    "swift": "swift",
    "kotlin": "kt",
    "scala": "scala",
    "rust": "rs",
    "php": "php",
    "racket": "rkt",
    "erlang": "erl",
    "elixir": "ex",
    "dart": "dart",
    "mysql": "sql",
    "mssql": "sql",
    "oraclesql": "sql",
    "pandas": "py",
}


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "unknown"


def language_extension(language: str) -> str:
    key = language.strip().lower().replace(" ", "")
    return LANGUAGE_EXTENSIONS.get(key, slugify(language) or "txt")


@dataclass(frozen=True)
class Submission:
    submission_id: str
    problem_id: int
    title: str
    title_slug: str
    language: str
    code: str
    status: str
    submitted_at: int
    runtime: str | None = None
    memory: str | None = None

    @property
    def problem_dir_name(self) -> str:
        return f"{self.problem_id:04d}-{self.title_slug}"

    @property
    def solution_filename(self) -> str:
        return f"solution.{language_extension(self.language)}"

    @property
    def leetcode_url(self) -> str:
        return f"https://leetcode.com/problems/{self.title_slug}/submissions/{self.submission_id}/"

    @property
    def submitted_at_iso(self) -> str:
        return datetime.fromtimestamp(self.submitted_at, tz=timezone.utc).isoformat()

    def problem_path(self, problems_root: str) -> PurePosixPath:
        return PurePosixPath(problems_root) / self.problem_dir_name

    def solution_path(self, problems_root: str) -> str:
        return str(self.problem_path(problems_root) / self.solution_filename)

    def metadata_path(self, problems_root: str) -> str:
        return str(self.problem_path(problems_root) / "metadata.json")

    def notes_path(self, problems_root: str) -> str:
        return str(self.problem_path(problems_root) / "notes.md")

    def identity_key(self) -> tuple[int, str]:
        return (self.problem_id, self.language.strip().lower())
