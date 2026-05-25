from __future__ import annotations

import json
from typing import Any


def latest_synced_timestamp(existing_files: dict[str, str]) -> int | None:
    timestamps = []
    for path, content in existing_files.items():
        if not path.endswith("/metadata.json"):
            continue
        timestamps.extend(_timestamps_from_metadata(content))
    return max(timestamps) if timestamps else None


def incremental_cutoff(existing_files: dict[str, str], lookback_seconds: int = 86400) -> int | None:
    latest = latest_synced_timestamp(existing_files)
    if latest is None:
        return None
    return max(0, latest - lookback_seconds)


def _timestamps_from_metadata(content: str) -> list[int]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, dict):
        return []

    timestamps = []
    for solution in _solution_records(parsed):
        timestamp = _coerce_timestamp(solution.get("submitted_at_unix"))
        if timestamp is not None:
            timestamps.append(timestamp)
    return timestamps


def _solution_records(metadata: dict[str, Any]) -> list[dict[str, Any]]:
    solutions = metadata.get("solutions")
    if isinstance(solutions, list):
        return [solution for solution in solutions if isinstance(solution, dict)]
    return [metadata]


def _coerce_timestamp(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None
