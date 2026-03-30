"""
NICK → TelegramUsername_WZ sync service.

Receives webhooks from amoCRM on lead status change.
If lead has NICK field filled — copies it to TelegramUsername_WZ
on the linked contact (with @ prefix). Prevents WhatsApp duplicates
when Wazzup dedup checks TelegramUsername_WZ.

Webhook URL: http://<server>:8586/webhook/nick-sync
"""

import os
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, Request, BackgroundTasks
import uvicorn

from amocrm import AmoCRM

load_dotenv()

# ── Config ──
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8586"))
LEAD_NICK_FIELD_ID = 1612133           # NICK field on leads (@username)
CONTACT_TG_USERNAME_WZ = 1648299       # TelegramUsername_WZ on contacts

# ── Logging ──
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("nick-sync")

# ── amoCRM client (shares tokens.json with tilda-note-webhook) ──
crm = AmoCRM(
    domain=os.getenv("AMOCRM_DOMAIN"),
    client_id=os.getenv("AMOCRM_CLIENT_ID"),
    client_secret=os.getenv("AMOCRM_CLIENT_SECRET"),
    redirect_uri=os.getenv("AMOCRM_REDIRECT_URI", "https://example.com"),
)

# ── Helpers ──

def extract_field(entity: dict, field_id: int) -> str | None:
    """Extract custom field value from an amoCRM entity."""
    for cf in entity.get("custom_fields_values") or []:
        if cf["field_id"] == field_id:
            vals = cf.get("values", [])
            if vals:
                return str(vals[0].get("value", "")).strip()
    return None


# ── FastAPI app ──

app = FastAPI(title="NICK Sync Service")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "has_token": bool(crm.access_token),
    }


@app.post("/webhook/nick-sync")
async def webhook_nick_sync(request: Request, background_tasks: BackgroundTasks):
    """
    amoCRM webhook: sync NICK → TelegramUsername_WZ.

    Triggered by: lead status change (configured in amoCRM).
    amoCRM sends form-encoded data:
      leads[status][0][id]=12345
      leads[status][0][status_id]=60971918
    """
    try:
        form = await request.form()
        data = dict(form)
    except Exception:
        body = await request.body()
        log.debug("Raw body: %s", body[:500])
        data = {}

    # Parse lead IDs from webhook events
    # AmoCRM sends leads[status][N][id] (status change) or leads[add][N][id] (creation)
    lead_ids = []
    for key, value in data.items():
        for prefix in ("leads[status]", "leads[add]"):
            if not key.startswith(prefix):
                continue
            parts = key.replace(f"{prefix}[", "").rstrip("]").split("][")
            if len(parts) == 2 and parts[1] == "id":
                try:
                    lid = int(value)
                    if lid:
                        lead_ids.append(lid)
                except (ValueError, TypeError):
                    pass
    # Deduplicate
    lead_ids = list(dict.fromkeys(lead_ids))

    if not lead_ids:
        log.debug("No lead IDs found (entries: %d)", len(lead_entries))
        return {"status": "ignored", "reason": "no lead IDs"}

    log.info("Processing %d leads: %s", len(lead_ids), lead_ids)

    for lid in lead_ids:
        background_tasks.add_task(process_nick_sync, lid)

    return {"status": "accepted", "leads": lead_ids}


def process_nick_sync(lead_id: int):
    """Copy NICK from lead to TelegramUsername_WZ on linked contact."""
    try:
        # 1. Get lead with contacts
        lead = crm.get(f"/leads/{lead_id}", {"with": "contacts"})
        if not lead:
            log.warning("Lead %d: cannot fetch", lead_id)
            return

        # 2. Extract NICK field
        nick_raw = extract_field(lead, LEAD_NICK_FIELD_ID)
        if not nick_raw or not nick_raw.strip():
            log.debug("Lead %d: NICK empty", lead_id)
            return

        # Normalize: strip, remove leading @, re-add @
        nick = nick_raw.strip().lstrip("@").strip()
        if not nick:
            log.debug("Lead %d: NICK only whitespace/@ ('%s')", lead_id, nick_raw)
            return
        nick = "@" + nick

        # 3. Get linked contact
        contacts = (lead.get("_embedded") or {}).get("contacts") or []
        if not contacts:
            log.debug("Lead %d: no linked contacts", lead_id)
            return

        contact_id = contacts[0]["id"]
        contact = crm.get(f"/contacts/{contact_id}")
        if not contact:
            log.warning("Lead %d: cannot fetch contact %d", lead_id, contact_id)
            return

        # 4. Check if TelegramUsername_WZ already filled
        existing_wz = extract_field(contact, CONTACT_TG_USERNAME_WZ)
        if existing_wz:
            log.debug("Lead %d: contact %d already has WZ=%s", lead_id, contact_id, existing_wz)
            return

        # 5. Copy NICK → TelegramUsername_WZ
        result = crm.patch(f"/contacts", [{
            "id": contact_id,
            "custom_fields_values": [{
                "field_id": CONTACT_TG_USERNAME_WZ,
                "values": [{"value": nick}],
            }],
        }])

        if result is not None:
            log.info("Lead %d: SYNCED %s → contact %d", lead_id, nick, contact_id)
        else:
            log.error("Lead %d: FAILED to patch contact %d", lead_id, contact_id)

    except Exception as e:
        log.error("Lead %d: %s", lead_id, e, exc_info=True)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
