import json

from leetcode_sync.metadata import incremental_cutoff, latest_synced_timestamp


def test_latest_synced_timestamp_reads_aggregate_metadata():
    files = {
        "problems/0001-two-sum/metadata.json": json.dumps(
            {
                "solutions": [
                    {"submitted_at_unix": 100},
                    {"submitted_at_unix": 300},
                ]
            }
        ),
        "problems/0002-add-two-numbers/metadata.json": json.dumps(
            {
                "solutions": [
                    {"submitted_at_unix": 200},
                ]
            }
        ),
    }

    assert latest_synced_timestamp(files) == 300


def test_latest_synced_timestamp_supports_old_single_metadata_shape():
    files = {
        "problems/0001-two-sum/metadata.json": json.dumps({"submitted_at_unix": "250"}),
    }

    assert latest_synced_timestamp(files) == 250


def test_latest_synced_timestamp_ignores_invalid_metadata():
    files = {
        "problems/0001-two-sum/metadata.json": "{not json",
        "problems/0002-add-two-numbers/metadata.json": json.dumps({"solutions": [{"missing": 1}]}),
        "problems/0003-longest-substring/solution.py": "code",
    }

    assert latest_synced_timestamp(files) is None


def test_incremental_cutoff_subtracts_lookback():
    files = {
        "problems/0001-two-sum/metadata.json": json.dumps({"solutions": [{"submitted_at_unix": 100000}]}),
    }

    assert incremental_cutoff(files, lookback_seconds=86400) == 13600


def test_incremental_cutoff_never_goes_negative():
    files = {
        "problems/0001-two-sum/metadata.json": json.dumps({"solutions": [{"submitted_at_unix": 100}]}),
    }

    assert incremental_cutoff(files, lookback_seconds=86400) == 0
