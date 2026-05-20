import unittest
import requests

from checkin import CheckinClient


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = ""

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error")

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self):
        self.headers = {}
        self.cookies = {}
        self.posts = []

    def get(self, url, timeout=None, **kwargs):
        return FakeResponse(status_code=403)

    def post(self, url, data=None, timeout=None, **kwargs):
        self.posts.append((url, data))
        if url.endswith("/auth/pow_challenge"):
            return FakeResponse(payload={
                "timestamp": 1,
                "ip": "127.0.0.1",
                "difficulty": 1,
                "salt": "salt",
                "signature": "sig",
            })
        return FakeResponse(payload={"ret": 1, "msg": "ok"})


class CheckinClientTests(unittest.TestCase):
    def test_login_adds_pow_fields_and_does_not_require_login_page_get(self):
        client = CheckinClient("https://example.com")
        client.session = FakeSession()

        self.assertTrue(client.login("user@example.com", "password"))

        _, login_data = client.session.posts[-1]
        self.assertEqual(login_data["email"], "user@example.com")
        self.assertEqual(login_data["passwd"], "password")
        self.assertIn("pow_nonce", login_data)
        self.assertEqual(login_data["pow_signature"], "sig")


if __name__ == "__main__":
    unittest.main()
