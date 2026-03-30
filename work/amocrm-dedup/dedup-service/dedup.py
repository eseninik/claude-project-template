"""Deduplication logic: NICK index + merge operations."""

import logging
import threading
import time

from config import (
    LEAD_NICK_FIELD_ID, CONTACT_LOGIN_FIELD_ID,
    CONTACT_UMNICO_SOCIAL_ID, AMOCRM_DOMAIN,
    MERGE_COOLDOWN_SECONDS, UMNICO_FIELD_IDS,
)

log = logging.getLogger("dedup")


def normalize_username(raw: str) -> str:
    if not raw:
        return ""
    return raw.strip().lstrip("@").lower().strip()


def extract_field(entity: dict, field_id: int) -> str | None:
    for cf in entity.get("custom_fields_values") or []:
        if cf["field_id"] == field_id:
            vals = cf.get("values", [])
            if vals:
                return str(vals[0].get("value", "")).strip()
    return None


class DedupEngine:
    """Maintains NICK→contact index and performs merges."""

    def __init__(self, crm):
        self.crm = crm
        self.nick_index = {}       # normalized_username → {contact_id, lead_ids}
        self._lock = threading.Lock()
        self._last_refresh = 0
        self._recent_merges = {}  # (old_id, new_id) -> timestamp

    # ── Index ──

    def build_index(self):
        """Scan all leads with NICK field, build username→contact mapping."""
        log.info("Building NICK index (full scan)...")
        start = time.time()

        leads = self.crm.get_all_pages("/leads", {"with": "contacts"}, "leads")
        log.info("Fetched %d leads total", len(leads))

        new_index = {}
        for lead in leads:
            nick = extract_field(lead, LEAD_NICK_FIELD_ID)
            if not nick:
                continue
            normalized = normalize_username(nick)
            if not normalized:
                continue

            contacts = (lead.get("_embedded") or {}).get("contacts") or []
            for c in contacts:
                cid = c["id"]
                if normalized not in new_index:
                    new_index[normalized] = {"contact_id": cid, "lead_ids": set()}
                new_index[normalized]["lead_ids"].add(lead["id"])

        with self._lock:
            self.nick_index = new_index
            self._last_refresh = time.time()

        elapsed = time.time() - start
        log.info("NICK index built: %d usernames in %.1fs", len(new_index), elapsed)

    def lookup(self, username: str) -> dict | None:
        """Find old contact by normalized username."""
        normalized = normalize_username(username)
        with self._lock:
            return self.nick_index.get(normalized)

    # ── Merge ──

    def check_and_merge(self, new_lead_id: int) -> dict:
        """
        Check if a new lead's contact is a duplicate and merge if so.
        Returns status dict.
        """
        result = {"new_lead_id": new_lead_id, "action": "none"}

        # 1. Get the new lead with its contacts
        new_lead = self.crm.get_lead(new_lead_id, with_contacts=True)
        if not new_lead:
            result["error"] = "cannot fetch new lead"
            return result

        contacts = (new_lead.get("_embedded") or {}).get("contacts") or []
        if not contacts:
            return result  # no contact linked — skip

        new_contact_id = contacts[0]["id"]

        # 2. Get the new contact, check if it has Umnico fields
        new_contact = self.crm.get_contact(new_contact_id, with_leads=True)
        if not new_contact:
            result["error"] = "cannot fetch new contact"
            return result

        login = extract_field(new_contact, CONTACT_LOGIN_FIELD_ID)
        umnico_id = extract_field(new_contact, CONTACT_UMNICO_SOCIAL_ID)

        if not login and not umnico_id:
            return result  # not an Umnico contact — skip

        result["new_contact_id"] = new_contact_id
        result["login"] = login

        if not login:
            result["action"] = "skip_no_login"
            return result

        # 3. Look up old contact by username
        match = self.lookup(login)
        if not match:
            result["action"] = "no_match"
            return result

        old_contact_id = match["contact_id"]

        # Don't merge with self
        if old_contact_id == new_contact_id:
            result["action"] = "same_contact"
            return result

        result["old_contact_id"] = old_contact_id
        result["action"] = "merge"

        # Cooldown: if same pair was merged recently, just close the lead
        pair_key = (old_contact_id, new_contact_id)
        now = time.time()
        if pair_key in self._recent_merges:
            elapsed = now - self._recent_merges[pair_key]
            if elapsed < MERGE_COOLDOWN_SECONDS:
                log.info(
                    "Cooldown: pair (%d, %d) merged %ds ago — closing lead %d without full merge",
                    old_contact_id, new_contact_id, int(elapsed), new_lead_id,
                )
                self.crm.close_lead_as_double(new_lead_id)
                result["action"] = "cooldown_close"
                return result

        # 4. Execute merge
        merge_result = self._execute_merge(old_contact_id, new_contact_id, new_lead_id, login)
        result.update(merge_result)

        return result

    def _execute_merge(self, old_id: int, new_id: int, new_lead_id: int, username: str) -> dict:
        """Execute merge: link lead, copy fields, close lead, unlink, add note."""
        steps = []

        old_contact = self.crm.get_contact(old_id, with_leads=True)
        new_contact = self.crm.get_contact(new_id, with_leads=True)
        if not old_contact or not new_contact:
            return {"status": "FAILED", "error": "cannot fetch contacts for merge"}

        new_lead_refs = (new_contact.get("_embedded") or {}).get("leads") or []
        new_lead_ids = [lr["id"] for lr in new_lead_refs]
        old_field_ids = {cf["field_id"] for cf in old_contact.get("custom_fields_values") or []}

        # Step 1: Link new leads to old contact
        if new_lead_ids:
            r = self.crm.link_leads_to_contact(old_id, new_lead_ids)
            steps.append(f"link:{len(new_lead_ids)} leads" if r is not None else "link:FAILED")

        # Step 2: Copy Umnico fields
        new_fields = new_contact.get("custom_fields_values") or []
        fields_to_copy = [
            {"field_id": cf["field_id"], "values": cf["values"]}
            for cf in new_fields
            if cf.get("values") and cf["field_id"] not in old_field_ids
        ]
        if fields_to_copy:
            r = self.crm.patch("/contacts", [{"id": old_id, "custom_fields_values": fields_to_copy}])
            steps.append(f"fields:{len(fields_to_copy)}" if r is not None else "fields:FAILED")

        # Step 2.5: Clear Umnico fields on NEW contact — forces Umnico to rebind to old contact
        r = self.crm.clear_contact_fields(new_id, UMNICO_FIELD_IDS)
        steps.append("clear_umnico:OK" if r is not None else "clear_umnico:FAILED")

        # Step 3: Close duplicate leads as Double
        for lid in new_lead_ids:
            lead = self.crm.get_lead(lid)
            if not lead or lead.get("status_id") == 143:
                continue
            self.crm.close_lead_as_double(lid)
        steps.append(f"closed:{len(new_lead_ids)} leads")

        # Step 4: Unlink from new contact
        if new_lead_ids:
            r = self.crm.unlink_leads_from_contact(new_id, new_lead_ids)
            steps.append("unlink:OK" if r is not None else "unlink:FAILED")

        # Step 4.5: Copy chat/notes from new contact to old contact's lead
        old_lead_refs = (old_contact.get("_embedded") or {}).get("leads") or []
        if old_lead_refs:
            old_lead_id = old_lead_refs[0]["id"]
            copied = self.crm.copy_chat_notes(new_id, old_lead_id)
            if copied > 0:
                steps.append(f"chat_copied:{copied} notes")

        # Step 5: Add note to old contact's lead
        if old_lead_refs:
            old_lead_id = old_lead_refs[0]["id"]
            lead_url = f"https://{AMOCRM_DOMAIN}/leads/detail/{new_lead_id}"
            contact_url = f"https://{AMOCRM_DOMAIN}/contacts/detail/{new_id}"
            note_text = (
                f"Автоматическая дедупликация\n\n"
                f"Найден дубль контакта по Telegram: @{username}\n"
                f"Дубль-сделка: {lead_url}\n"
                f"Дубль-контакт: {contact_url}\n\n"
                f"Выполнено: сделки привязаны, поля скопированы, "
                f"дубль-сделка закрыта как Double."
            )
            self.crm.add_note("leads", old_lead_id, note_text)
            steps.append("note:OK")

        # Update index with new username
        normalized = normalize_username(username)
        with self._lock:
            if normalized in self.nick_index:
                self.nick_index[normalized]["lead_ids"].update(new_lead_ids)

        # Update cooldown cache
        pair_key = (old_id, new_id)
        self._recent_merges[pair_key] = time.time()

        # Cleanup old cooldown entries (older than 2x cooldown)
        cutoff = time.time() - (MERGE_COOLDOWN_SECONDS * 2)
        self._recent_merges = {k: v for k, v in self._recent_merges.items() if v > cutoff}

        return {"status": "MERGED", "steps": steps}
