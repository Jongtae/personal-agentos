import tempfile
import unittest
from urllib.parse import parse_qs, urlparse

from personal_agent.drive_web_oauth import DRIVE_FILE, DriveScopeError, DriveWebOAuthError, DriveWebOAuthHandoff
from personal_agent.quickstart_store import QuickStore


class DriveWebOAuthTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = QuickStore(self.temp.name)
        self.clock = [1000]
        self.flow = DriveWebOAuthHandoff(self.store, "web-client", "https://connect.example.test/oauth/callback", "https://connect.example.test", now=lambda: self.clock[0])

    def tearDown(self):
        self.temp.cleanup()

    def begin(self):
        offer = self.flow.begin(42)
        return offer, parse_qs(urlparse(offer["button"]["url"]).query)["state"][0]

    def connect(self):
        _offer, state = self.begin()
        return self.flow.complete({"state": state, "code": "short-code"}, 42, lambda request: {"access_token": "access-secret", "refresh_token": "refresh-secret", "scope": DRIVE_FILE, "expires_in": 60})

    def test_telegram_offer_is_https_and_oauth_uses_pkce_and_drive_file_only(self):
        offer, state = self.begin()
        self.assertEqual(offer["button"]["text"], "Google Drive 연결하기")
        self.assertTrue(offer["button"]["url"].startswith("https://"))
        self.assertNotIn("verifier", offer["button"]["url"])
        query = parse_qs(urlparse(self.flow.authorization_url(state, 42)).query)
        self.assertEqual(query["scope"], [DRIVE_FILE])
        self.assertEqual(query["code_challenge_method"], ["S256"])
        self.assertNotIn("code_verifier", query)

    def test_callback_is_owner_bound_single_use_and_redacts_tokens_from_status(self):
        self.assertEqual(self.connect()["state"], "connected")
        self.assertNotIn("secret", str(self.flow.status()))
        self.assertIn("access-secret", str(self.store.secret("drive_web_oauth_tokens")))
        with self.assertRaises(DriveWebOAuthError):
            self.flow.complete({"state": "replay", "code": "again"}, 42, lambda _: {})

    def test_wrong_owner_denial_expiry_and_failed_callback_recover_without_tokens(self):
        _offer, state = self.begin()
        with self.assertRaises(DriveWebOAuthError): self.flow.authorization_url(state, 99)
        with self.assertRaises(DriveWebOAuthError): self.flow.complete({"state": state, "error": "access_denied"}, 42, lambda _: {})
        self.assertEqual(self.flow.status()["state"], "denied")
        _offer, state = self.begin(); self.clock[0] += 601
        with self.assertRaises(DriveWebOAuthError): self.flow.authorization_url(state, 42)
        self.assertEqual(self.flow.status()["state"], "expired")
        self.assertEqual(self.store.secret("drive_web_oauth_tokens"), "")

    def test_only_picker_selected_files_can_be_read_and_full_drive_search_is_blocked(self):
        self.connect()
        with self.assertRaises(DriveScopeError): self.flow.search("plan")
        with self.assertRaises(DriveScopeError): self.flow.assert_selected(42, "unselected")
        selected = self.flow.select_files(42, [{"id": "picked", "name": "meeting plan"}])
        self.assertEqual(selected["files"], [{"id": "picked", "name": "meeting plan"}])
        self.assertTrue(self.flow.assert_selected(42, "picked"))

    def test_expired_access_token_requires_reauthentication(self):
        self.connect(); self.clock[0] += 61
        with self.assertRaisesRegex(DriveWebOAuthError, "expired"):
            self.flow.select_files(42, [{"id": "picked"}])
        self.assertEqual(self.flow.status()["state"], "reauth-required")


if __name__ == "__main__":
    unittest.main()
