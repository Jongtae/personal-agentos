"""Owner-local web OAuth handoff for explicitly selected Google Drive files.

The HTTPS link is a browser entry point only.  This module deliberately has
no control-plane persistence: state, PKCE verifier, callback code exchange,
and tokens stay in the owner's local runtime.
"""
import base64
import hashlib
import secrets
import time
from urllib.parse import urlencode


DRIVE_FILE = "https://www.googleapis.com/auth/drive.file"
AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
PENDING_KEY = "drive_web_oauth_pending"
TOKEN_KEY = "drive_web_oauth_tokens"
STATUS_KEY = "drive_web_oauth_status"
SELECTED_FILES_KEY = "drive_web_oauth_selected_files"


class DriveWebOAuthError(ValueError):
    pass


class DriveScopeError(DriveWebOAuthError):
    pass


def _pkce_pair():
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode()).digest()
    return verifier, base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


class DriveWebOAuthHandoff:
    """One-time OAuth state bound to one paired Telegram owner.

    ``store`` must be an owner-local encrypted secret store in production.
    It needs ``secret(key[, value])`` and ``put(key, value)`` methods.  The
    public handoff URL is opaque and never contains a token, code, verifier,
    Telegram message, or file content.
    """
    def __init__(self, store, client_id, redirect_uri, handoff_url, now=time.time, ttl_seconds=600):
        if not all(isinstance(value, str) and value for value in (client_id, redirect_uri, handoff_url)):
            raise ValueError("Web OAuth client, callback, and HTTPS handoff URL are required.")
        if not handoff_url.startswith("https://") or not redirect_uri.startswith("https://"):
            raise ValueError("Web OAuth handoff and callback URLs must use HTTPS.")
        self.store, self.client_id = store, client_id
        self.redirect_uri, self.handoff_url = redirect_uri, handoff_url.rstrip("/")
        self.now, self.ttl_seconds = now, ttl_seconds

    def begin(self, telegram_owner_id):
        if not isinstance(telegram_owner_id, int) or telegram_owner_id <= 0:
            raise DriveWebOAuthError("A paired Telegram owner is required.")
        verifier, challenge = _pkce_pair()
        state = secrets.token_urlsafe(32)
        created = self.now()
        pending = {"state": state, "verifier": verifier, "owner": telegram_owner_id,
                   "created_at": created, "expires_at": created + self.ttl_seconds, "status": "pending"}
        self.store.secret(PENDING_KEY, pending)
        self._audit("connection-offered")
        return {
            "state": "connection-required",
            "message": "Google Drive 연결이 필요합니다. 선택한 파일만 읽을 수 있으며 전체 Drive 검색은 하지 않습니다.",
            "button": {"text": "Google Drive 연결하기", "url": self.handoff_url + "/google-drive?" + urlencode({"state": state})},
            "expires_at": pending["expires_at"],
            "code_challenge": challenge,
        }

    def authorization_url(self, state, telegram_owner_id):
        pending = self._pending(state, telegram_owner_id)
        query = urlencode({"client_id": self.client_id, "redirect_uri": self.redirect_uri,
                           "response_type": "code", "scope": DRIVE_FILE, "access_type": "offline",
                           "code_challenge": self._challenge(pending["verifier"]),
                           "code_challenge_method": "S256", "state": pending["state"]})
        return AUTHORIZATION_ENDPOINT + "?" + query

    def complete(self, callback, telegram_owner_id, exchange):
        if not isinstance(callback, dict):
            raise DriveWebOAuthError("Google callback is invalid.")
        pending = self._pending(callback.get("state"), telegram_owner_id)
        if callback.get("error"):
            self._finish("denied")
            raise DriveWebOAuthError("Google Drive access was not approved.")
        code = callback.get("code")
        if not isinstance(code, str) or not code:
            self._finish("callback-failed")
            raise DriveWebOAuthError("Google Drive authorization code is missing.")
        response = exchange({"code": code, "code_verifier": pending["verifier"],
                             "redirect_uri": self.redirect_uri, "client_id": self.client_id})
        if not isinstance(response, dict) or not isinstance(response.get("access_token"), str):
            self._finish("callback-failed")
            raise DriveWebOAuthError("Google Drive token exchange failed.")
        granted = str(response.get("scope", ""))
        if DRIVE_FILE not in granted.split():
            self._finish("scope-rejected")
            raise DriveScopeError("Google Drive file-selection scope was not granted.")
        tokens = {key: response[key] for key in ("access_token", "refresh_token", "expires_in", "scope") if key in response}
        if isinstance(tokens.get("expires_in"), (int, float)):
            tokens["expires_at"] = self.now() + max(0, tokens["expires_in"])
        self.store.secret(TOKEN_KEY, tokens)
        self._finish("connected")
        return self.status()

    def select_files(self, telegram_owner_id, files):
        self._connected(telegram_owner_id)
        if not isinstance(files, list) or not files or len(files) > 20:
            raise DriveScopeError("Choose one to twenty files in Google Picker.")
        selected = []
        for item in files:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
                raise DriveScopeError("Google Picker returned an invalid file.")
            selected.append({"id": item["id"], "name": str(item.get("name", ""))[:240]})
        self.store.put(SELECTED_FILES_KEY, {"owner": telegram_owner_id, "files": selected})
        self._audit("files-selected")
        return {"state": "files-selected", "files": selected}

    def assert_selected(self, telegram_owner_id, file_id):
        self._connected(telegram_owner_id)
        selected = self.store.config(SELECTED_FILES_KEY, {})
        if selected.get("owner") != telegram_owner_id or file_id not in {row["id"] for row in selected.get("files", [])}:
            raise DriveScopeError("Choose this file in Google Picker before reading it.")
        return True

    def search(self, *_args, **_kwargs):
        raise DriveScopeError("drive.file does not allow arbitrary or full-Drive search; choose a file first.")

    def status(self):
        value = self.store.config(STATUS_KEY, {"state": "disconnected", "audit": []})
        return {"state": value.get("state", "disconnected"), "audit": list(value.get("audit", []))}

    def _pending(self, state, owner):
        pending = self.store.secret(PENDING_KEY)
        if not isinstance(pending, dict) or pending.get("status") != "pending":
            raise DriveWebOAuthError("No pending Google Drive connection exists.")
        if not isinstance(state, str) or not secrets.compare_digest(state, str(pending.get("state", ""))):
            raise DriveWebOAuthError("Google Drive authorization state did not match.")
        if owner != pending.get("owner"):
            raise DriveWebOAuthError("This Drive connection belongs to another Telegram owner.")
        if self.now() >= pending.get("expires_at", 0):
            self._finish("expired")
            raise DriveWebOAuthError("Google Drive connection link expired; request a new link.")
        return pending

    @staticmethod
    def _challenge(verifier):
        return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()

    def _connected(self, owner):
        tokens = self.store.secret(TOKEN_KEY)
        if not isinstance(tokens, dict) or not tokens.get("access_token"):
            raise DriveWebOAuthError("Google Drive is not connected.")
        if isinstance(tokens.get("expires_at"), (int, float)) and self.now() >= tokens["expires_at"]:
            self._finish("reauth-required")
            raise DriveWebOAuthError("Google Drive authorization expired; reconnect required.")
        if self.store.config(SELECTED_FILES_KEY, {}).get("owner") not in (None, owner):
            raise DriveWebOAuthError("This Drive connection belongs to another Telegram owner.")

    def _finish(self, state):
        self.store.secret(PENDING_KEY, {"status": "used"})
        self._audit(state)

    def _audit(self, event):
        prior = self.status()
        self.store.put(STATUS_KEY, {"state": event, "audit": [*prior["audit"], event][-50:]})
