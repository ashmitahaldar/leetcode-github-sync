from leetcode_sync.secrets import Redactor


def test_redactor_removes_known_secrets():
    redactor = Redactor(["lc-secret", "gh-secret"])

    message = redactor.redact("failed with lc-secret and gh-secret")

    assert "lc-secret" not in message
    assert "gh-secret" not in message
    assert message == "failed with [REDACTED] and [REDACTED]"
