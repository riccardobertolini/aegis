"""Security API client methods."""
from __future__ import annotations

from .base import AegisClient


class SecurityMixin(AegisClient):
    """Methods for /security endpoints."""

    BASE = "/security"

    def login(self, username: str, password: str) -> dict:
        """POST /security/login (form-encoded, OAuth2 compatible)"""
        import httpx
        with httpx.Client(base_url=self.base_url, timeout=self._timeout) as c:
            r = c.post(
                f"{self.BASE}/login",
                data={"username": username, "password": password},
            )
            r.raise_for_status()
            payload = r.json()
            # auto-set token for subsequent calls
            self._token = payload.get("access_token")
            self._headers["Authorization"] = f"Bearer {self._token}"
            return payload

    def logout(self) -> None:
        """POST /security/logout"""
        self._post(f"{self.BASE}/logout")
        self._token = None
        self._headers.pop("Authorization", None)

    def list_sessions(self) -> list[dict]:
        """GET /security/sessions"""
        return self._get(f"{self.BASE}/sessions")

    def revoke_session(self, session_id: str) -> None:
        """DELETE /security/sessions/{session_id}"""
        self._delete(f"{self.BASE}/sessions/{session_id}")

    def create_user(self, username: str, password: str, role_names: list[str] | None = None) -> dict:
        """POST /security/users"""
        return self._post(
            f"{self.BASE}/users",
            json={"username": username, "password": password, "role_names": role_names or ["viewer"]},
        )

    def list_users(self, active_only: bool = True) -> list[dict]:
        """GET /security/users"""
        return self._get(f"{self.BASE}/users", active_only=active_only)

    def query_audit(
        self,
        user_id: str | None = None,
        action: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """GET /security/audit"""
        params: dict = {"limit": limit}
        if user_id:
            params["user_id"] = user_id
        if action:
            params["action"] = action
        return self._get(f"{self.BASE}/audit", **params)

    def verify_audit_chain(self) -> dict:
        """POST /security/audit/verify"""
        return self._post(f"{self.BASE}/audit/verify")

    def rotate_key(self, new_passphrase: str | None = None) -> dict:
        """POST /security/keys/rotate"""
        return self._post(f"{self.BASE}/keys/rotate", json={"new_passphrase": new_passphrase})
