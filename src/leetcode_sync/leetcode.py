from __future__ import annotations

from typing import Any

from .errors import AuthError, RemoteApiError
from .http import HttpClient
from .models import Submission, slugify
from .secrets import SecretBundle


SUBMISSION_LIST_QUERY = """
query submissionList($offset: Int!, $limit: Int!, $lastKey: String) {
  submissionList(offset: $offset, limit: $limit, lastKey: $lastKey) {
    lastKey
    hasNext
    submissions {
      id
      title
      titleSlug
      statusDisplay
      lang
      timestamp
      runtime
      memory
    }
  }
}
"""

SUBMISSION_DETAILS_QUERY = """
query submissionDetails($submissionId: Int!) {
  submissionDetails(submissionId: $submissionId) {
    id
    code
    runtime
    memory
    timestamp
    statusDisplay
    lang {
      name
    }
    question {
      questionFrontendId
      title
      titleSlug
    }
  }
}
"""

VIEWER_QUERY = """
query globalData {
  userStatus {
    isSignedIn
    username
  }
}
"""


class LeetCodeClient:
    endpoint = "https://leetcode.com/graphql"

    def __init__(self, secrets: SecretBundle, http: HttpClient):
        self.secrets = secrets
        self.http = http

    def validate_auth(self) -> str:
        data = self._graphql(VIEWER_QUERY, {})
        status = data.get("userStatus") or {}
        if not status.get("isSignedIn"):
            raise AuthError("LeetCode session is not signed in")
        return str(status.get("username") or "unknown")

    def fetch_accepted_submissions(self, page_size: int = 50, since_timestamp: int | None = None) -> list[Submission]:
        submissions: list[Submission] = []
        offset = 0
        last_key = None

        while True:
            payload = self._graphql(
                SUBMISSION_LIST_QUERY,
                {"offset": offset, "limit": page_size, "lastKey": last_key},
            )
            page = payload.get("submissionList") or {}
            raw_submissions = page.get("submissions") or []
            if not isinstance(raw_submissions, list):
                raise RemoteApiError("LeetCode returned an invalid submissions payload")

            for raw in raw_submissions:
                if str(raw.get("statusDisplay", "")).lower() != "accepted":
                    continue
                if since_timestamp is not None and int(raw.get("timestamp", 0)) < since_timestamp:
                    continue
                submissions.append(self.fetch_submission_details(str(raw.get("id"))))

            has_next = bool(page.get("hasNext")) or bool(page.get("lastKey"))
            last_key = page.get("lastKey")
            if not has_next:
                break
            offset += page_size

        return submissions

    def fetch_submission_details(self, submission_id: str) -> Submission:
        payload = self._graphql(SUBMISSION_DETAILS_QUERY, {"submissionId": int(submission_id)})
        details = payload.get("submissionDetails")
        if not isinstance(details, dict):
            raise RemoteApiError(f"LeetCode did not return details for submission {submission_id}")
        return self._normalize_submission(details)

    def _graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Cookie": self._cookie_header(),
            "Origin": "https://leetcode.com",
            "Referer": "https://leetcode.com/",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "x-requested-with": "XMLHttpRequest",
        }
        if self.secrets.csrf_token:
            headers["x-csrftoken"] = self.secrets.csrf_token
        response = self.http.request_json(
            "POST",
            self.endpoint,
            headers=headers,
            body={"query": query, "variables": variables},
        )
        if "errors" in response.data:
            raise RemoteApiError(f"LeetCode GraphQL error: {response.data['errors']}")
        data = response.data.get("data")
        if not isinstance(data, dict):
            raise RemoteApiError("LeetCode returned a response without data")
        return data

    def _cookie_header(self) -> str:
        parts = [f"LEETCODE_SESSION={self.secrets.leetcode_session}"]
        if self.secrets.csrf_token:
            parts.append(f"csrftoken={self.secrets.csrf_token}")
        return "; ".join(parts)

    @staticmethod
    def _normalize_submission(raw: dict[str, Any]) -> Submission:
        question = raw.get("question") if isinstance(raw.get("question"), dict) else {}
        title = str(question.get("title") or raw.get("title") or "Unknown")
        title_slug = str(question.get("titleSlug") or raw.get("titleSlug") or slugify(title))
        frontend_id = str(question.get("questionFrontendId") or raw.get("questionFrontendId") or "0")
        problem_id = int("".join(ch for ch in frontend_id if ch.isdigit()) or "0")
        language = raw.get("lang")
        if isinstance(language, dict):
            language = language.get("name")
        return Submission(
            submission_id=str(raw.get("id") or raw.get("submissionId")),
            problem_id=problem_id,
            title=title,
            title_slug=title_slug,
            language=str(language or "unknown"),
            code=str(raw.get("code") or ""),
            status=str(raw.get("statusDisplay") or raw.get("status") or "Accepted"),
            submitted_at=int(raw.get("timestamp") or 0),
            runtime=raw.get("runtime"),
            memory=raw.get("memory"),
        )
