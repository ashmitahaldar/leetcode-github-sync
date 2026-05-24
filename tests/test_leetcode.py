from leetcode_sync.errors import RemoteApiError
from leetcode_sync.leetcode import LeetCodeClient
from leetcode_sync.secrets import SecretBundle


class CapturingHttp:
    def __init__(self):
        self.headers = {}

    def request_json(self, method, url, headers=None, body=None):
        self.headers = headers or {}
        return type("Response", (), {"data": {"errors": ["stop"]}})()


def test_graphql_sends_browser_and_csrf_headers():
    http = CapturingHttp()
    client = LeetCodeClient(
        secrets=SecretBundle(leetcode_session="session", csrf_token="csrf", github_token="github"),
        http=http,
    )

    try:
        client.validate_auth()
    except RemoteApiError:
        pass

    assert http.headers["Origin"] == "https://leetcode.com"
    assert http.headers["Referer"] == "https://leetcode.com/"
    assert http.headers["x-csrftoken"] == "csrf"
    assert "LEETCODE_SESSION=session" in http.headers["Cookie"]
    assert "csrftoken=csrf" in http.headers["Cookie"]
    assert "Mozilla/5.0" in http.headers["User-Agent"]
