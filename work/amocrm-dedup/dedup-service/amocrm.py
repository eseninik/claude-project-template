"""amoCRM API client with automatic token refresh."""

import json
import time
import logging
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from config import (
    AMOCRM_BASE_URL, AMOCRM_DOMAIN, AMOCRM_CLIENT_ID,
    AMOCRM_CLIENT_SECRET, AMOCRM_REDIRECT_URI, TOKEN_FILE,
)

log = logging.getLogger("amocrm")


class AmoCRM:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = 0
        self._load_tokens()

    # ── Token management ──

    def _load_tokens(self):
        path = Path(TOKEN_FILE)
        if path.exists():
            data = json.loads(path.read_text())
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            self.token_expires_at = data.get("expires_at", 0)
            log.info("Tokens loaded from %s", TOKEN_FILE)
        else:
            log.warning("No token file found at %s — need initial tokens", TOKEN_FILE)

    def _save_tokens(self):
        Path(TOKEN_FILE).write_text(json.dumps({
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.token_expires_at,
        }))
        log.info("Tokens saved to %s", TOKEN_FILE)

    def refresh_access_token(self):
        """Refresh OAuth token. Returns True on success."""
        if not self.refresh_token:
            log.error("No refresh token available")
            return False

        url = f"https://{AMOCRM_DOMAIN}/oauth2/access_token"
        payload = json.dumps({
            "client_id": AMOCRM_CLIENT_ID,
            "client_secret": AMOCRM_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "redirect_uri": AMOCRM_REDIRECT_URI,
        }).encode()

        req = Request(url, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urlopen(req) as resp:
                data = json.loads(resp.read().decode())
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
            self.token_expires_at = time.time() + data.get("expires_in", 86400) - 300
            self._save_tokens()
            log.info("Token refreshed successfully")
            return True
        except HTTPError as e:
            body = e.read().decode()[:500]
            log.error("Token refresh failed: %s %s", e.code, body)
            return False

    def _ensure_token(self):
        if time.time() > self.token_expires_at:
            log.info("Token expired or expiring soon, refreshing...")
            self.refresh_access_token()

    # ── HTTP methods ──

    def _request(self, method: str, path: str, data=None, params: dict = None):
        self._ensure_token()

        url = f"{AMOCRM_BASE_URL}{path}"
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
            if query:
                url += f"?{query}"

        body = json.dumps(data).encode() if data else None
        req = Request(url, data=body, method=method, headers={
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        })

        try:
            with urlopen(req) as resp:
                raw = resp.read().decode()
                time.sleep(0.15)  # rate limit
                if not raw.strip():
                    return {}
                return json.loads(raw)
        except HTTPError as e:
            if e.code == 204:
                return {}
            if e.code == 429:
                log.warning("Rate limited, waiting 3s...")
                time.sleep(3)
                return self._request(method, path, data, params)
            if e.code == 401:
                log.warning("Got 401, trying token refresh...")
                if self.refresh_access_token():
                    return self._request(method, path, data, params)
            body = e.read().decode()[:300]
            log.error("API %s %s → %s: %s", method, path, e.code, body)
            return None

    def get(self, path: str, params: dict = None):
        return self._request("GET", path, params=params)

    def post(self, path: str, data):
        return self._request("POST", path, data=data)

    def patch(self, path: str, data):
        return self._request("PATCH", path, data=data)

    # ── High-level helpers ──

    def get_contact(self, contact_id: int, with_leads: bool = False):
        params = {"with": "leads"} if with_leads else {}
        return self.get(f"/contacts/{contact_id}", params)

    def get_lead(self, lead_id: int, with_contacts: bool = False):
        params = {"with": "contacts"} if with_contacts else {}
        return self.get(f"/leads/{lead_id}", params)

    def get_all_pages(self, path: str, params: dict = None, embed_key: str = None):
        """Fetch all pages of a paginated endpoint."""
        results = []
        page = 1
        base_params = dict(params or {})

        while True:
            base_params["page"] = str(page)
            base_params["limit"] = "250"
            data = self.get(path, base_params)
            if not data or "_embedded" not in data:
                break

            key = embed_key or list(data["_embedded"].keys())[0]
            batch = data["_embedded"][key]
            results.extend(batch)

            if "next" not in data.get("_links", {}):
                break
            page += 1

        return results

    def add_note(self, entity_type: str, entity_id: int, text: str):
        """Add a text note to a lead or contact."""
        return self.post(f"/{entity_type}/{entity_id}/notes", [
            {"note_type": "common", "params": {"text": text}}
        ])

    def link_leads_to_contact(self, contact_id: int, lead_ids: list):
        data = [{"to_entity_id": lid, "to_entity_type": "leads"} for lid in lead_ids]
        return self.post(f"/contacts/{contact_id}/link", data)

    def unlink_leads_from_contact(self, contact_id: int, lead_ids: list):
        data = [{"to_entity_id": lid, "to_entity_type": "leads"} for lid in lead_ids]
        return self.post(f"/contacts/{contact_id}/unlink", data)

    def close_lead_as_double(self, lead_id: int):
        from config import CLOSED_STATUS_ID, LOSS_REASON_FIELD_ID, LOSS_REASON_DOUBLE_ENUM
        return self.patch("/leads", [{
            "id": lead_id,
            "status_id": CLOSED_STATUS_ID,
            "custom_fields_values": [{
                "field_id": LOSS_REASON_FIELD_ID,
                "values": [{"enum_id": LOSS_REASON_DOUBLE_ENUM}]
            }]
        }])

    def clear_contact_fields(self, contact_id: int, field_ids: list):
        """Clear specific custom fields on a contact by setting empty values."""
        clear_data = [{"field_id": fid, "values": []} for fid in field_ids]
        return self.patch("/contacts", [{"id": contact_id, "custom_fields_values": clear_data}])

    def get_entity_notes(self, entity_type: str, entity_id: int, limit: int = 250) -> list:
        """Fetch all notes for an entity (contact or lead)."""
        data = self.get(f"/{entity_type}/{entity_id}/notes", {"limit": str(limit)})
        if data and "_embedded" in data:
            return data["_embedded"]["notes"]
        return []

    def copy_chat_notes(self, from_contact_id: int, to_lead_id: int) -> int:
        """Copy chat/text notes from a contact to a lead.

        Copies common (text) notes and Umnico service notes from the
        source contact to the target lead, preserving conversation history.
        Returns number of notes copied.
        """
        notes = self.get_entity_notes("contacts", from_contact_id)
        if not notes:
            return 0

        copied = 0
        for note in notes:
            note_type = note.get("note_type", "")
            # Copy common text notes and service messages
            if note_type == "common":
                text = (note.get("params") or {}).get("text", "")
                if text:
                    self.add_note("leads", to_lead_id, f"[Из дубль-контакта {from_contact_id}]\n{text}")
                    copied += 1
            elif note_type == "service_message":
                text = (note.get("params") or {}).get("text", "")
                if text:
                    self.add_note("leads", to_lead_id, f"[Чат из дубль-контакта {from_contact_id}]\n{text}")
                    copied += 1
        return copied
