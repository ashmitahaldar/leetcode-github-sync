from leetcode_sync.errors import RemoteApiError
from leetcode_sync.leetcode import LeetCodeClient
from leetcode_sync.secrets import SecretBundle


class CapturingHttp:
    def __init__(self):
        self.headers = {}

    def request_json(self, method, url, headers=None, body=None):
        self.headers = headers or {}
        return type("Response", (), {"data": {"errors": ["stop"]}})()


class PagingHttp:
    def __init__(self):
        self.bodies = []

    def request_json(self, method, url, headers=None, body=None):
        self.bodies.append(body or {})
        query = body["query"]
        if "submissionList" in query:
            assert "code" not in query
            assert "question" not in query
            return type(
                "Response",
                (),
                {
                    "data": {
                        "data": {
                            "submissionList": {
                                "lastKey": None,
                                "hasNext": False,
                                "submissions": [
                                    {
                                        "id": "123",
                                        "title": "Two Sum",
                                        "titleSlug": "two-sum",
                                        "statusDisplay": "Accepted",
                                        "lang": "python3",
                                        "timestamp": 100,
                                        "runtime": "40 ms",
                                        "memory": "16 MB",
                                    }
                                ],
                            }
                        }
                    }
                },
            )()
        return type(
            "Response",
            (),
            {
                "data": {
                    "data": {
                        "submissionDetails": {
                            "id": "123",
                            "code": "class Solution:\n    pass",
                            "runtime": "40 ms",
                            "memory": "16 MB",
                            "timestamp": 100,
                            "statusDisplay": "Accepted",
                            "lang": {"name": "python3"},
                            "question": {
                                "questionFrontendId": "1",
                                "title": "Two Sum",
                                "titleSlug": "two-sum",
                            },
                        }
                    }
                }
            },
        )()


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


def test_fetch_accepted_submissions_hydrates_details():
    http = PagingHttp()
    client = LeetCodeClient(
        secrets=SecretBundle(leetcode_session="session", csrf_token="csrf", github_token="github"),
        http=http,
    )

    submissions = client.fetch_accepted_submissions()

    assert len(submissions) == 1
    assert submissions[0].submission_id == "123"
    assert submissions[0].code.startswith("class Solution")
    assert submissions[0].problem_id == 1
    assert len(http.bodies) == 2
