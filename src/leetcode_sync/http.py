from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .errors import ApiResponseError, AuthError, RateLimitError, RemoteApiError


@dataclass(frozen=True)
class JsonResponse:
    status: int
    data: dict[str, Any]


class HttpClient:
    def __init__(self, max_retries: int = 3, request_delay_seconds: float = 0.35):
        self.max_retries = max_retries
        self.request_delay_seconds = request_delay_seconds

    def request_json(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
    ) -> JsonResponse:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        request_headers = {"Accept": "application/json", **(headers or {})}
        if body is not None:
            request_headers["Content-Type"] = "application/json"

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            if self.request_delay_seconds:
                time.sleep(self.request_delay_seconds)
            try:
                req = Request(url=url, data=payload, headers=request_headers, method=method.upper())
                with urlopen(req, timeout=30) as response:
                    raw = response.read().decode("utf-8")
                    return JsonResponse(status=response.status, data=json.loads(raw) if raw else {})
            except HTTPError as exc:
                if exc.code in {401, 403}:
                    raise AuthError(
                        f"Authentication failed for {url}: HTTP {exc.code}. "
                        "For LeetCode, refresh LEETCODE_SESSION and CSRFTOKEN from the same logged-in browser session."
                    ) from exc
                if exc.code == 429:
                    raise RateLimitError(f"Rate limited by {url}: HTTP 429") from exc
                if exc.code < 500 or attempt == self.max_retries:
                    detail = exc.read().decode("utf-8", errors="replace")
                    raise ApiResponseError(
                        f"Request failed for {url}: HTTP {exc.code} {detail}",
                        status=exc.code,
                        detail=detail,
                    ) from exc
                last_error = exc
            except (URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt == self.max_retries:
                    raise RemoteApiError(f"Request failed for {url}: {exc}") from exc
            time.sleep(min(2**attempt, 8))

        raise RemoteApiError(f"Request failed for {url}: {last_error}")
