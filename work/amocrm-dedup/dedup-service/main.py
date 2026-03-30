"""
amoCRM Dedup Service — automatic duplicate detection & merge.

Receives webhooks from amoCRM when a lead moves to "New" status.
If the lead's contact is from Umnico and matches an existing contact by
Telegram username, auto-merges and leaves a note on the original deal.

Webhook trigger: lead status change (Неразобранное → New).
"""

import logging
import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, BackgroundTasks
import uvicorn

from config import (
    SERVICE_HOST, SERVICE_PORT, INDEX_REFRESH_INTERVAL, LOG_LEVEL,
    MAIN_PIPELINE_ID, LEAD_NICK_FIELD_ID, CONTACT_TG_USERNAME_WZ,
)
from amocrm import AmoCRM
from dedup import DedupEngine, extract_field

# ── Logging ──
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("main")

# ── Global instances ──
crm = AmoCRM()
engine = DedupEngine(crm)


# ── Background index refresh ──

def index_refresh_loop():
    """Periodically refresh the NICK index."""
    while True:
        try:
            engine.build_index()
        except Exception as e:
            log.error("Index refresh failed: %s", e)
        time.sleep(INDEX_REFRESH_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: build index, start refresh thread
    log.info("Starting dedup service...")
    try:
        engine.build_index()
    except Exception as e:
        log.error("Initial index build failed: %s — will retry in background", e)

    refresh_thread = threading.Thread(target=index_refresh_loop, daemon=True)
    refresh_thread.start()
    log.info("Index refresh thread started (interval: %ds)", INDEX_REFRESH_INTERVAL)

    yield

    log.info("Shutting down dedup service")


# ── FastAPI app ──

app = FastAPI(title="amoCRM Dedup Service", lifespan=lifespan)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "index_size": len(engine.nick_index),
        "last_refresh": engine._last_refresh,
        "has_token": bool(crm.access_token),
    }


@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    """
    amoCRM webhook endpoint.

    Triggered by: lead status change (Смена статуса сделки).
    amoCRM sends POST with form-encoded data like:
      leads[status][0][id]=12345
      leads[status][0][pipeline_id]=7323650
      leads[status][0][status_id]=60971918

    We only process leads that moved into "New" status in the main pipeline.
    """
    # New status IDs across pipelines where Umnico leads can land
    NEW_STATUS_IDS = {
        60971918,   # Воронка → New
        72197930,   # Варламов → NEW
        75969022,   # International → New
    }

    try:
        form = await request.form()
        data = dict(form)
    except Exception:
        body = await request.body()
        log.debug("Raw webhook body: %s", body[:500])
        data = {}

    # Parse lead IDs from status change events
    # Format: leads[status][N][id], leads[status][N][status_id], leads[status][N][pipeline_id]
    lead_entries = {}  # index → {id, status_id, pipeline_id}
    for key, value in data.items():
        if not key.startswith("leads[status]"):
            continue
        # Extract index and field: leads[status][0][id] → (0, "id")
        parts = key.replace("leads[status][", "").rstrip("]").split("][")
        if len(parts) == 2:
            idx, field = parts
            lead_entries.setdefault(idx, {})[field] = value

    # Filter: only leads that moved to "New" status
    lead_ids = []
    for idx, entry in lead_entries.items():
        try:
            lid = int(entry.get("id", 0))
            status = int(entry.get("status_id", 0))
        except (ValueError, TypeError):
            continue
        if status in NEW_STATUS_IDS and lid:
            lead_ids.append(lid)

    if not lead_ids:
        log.debug("Webhook: no leads moved to New status (entries: %d)", len(lead_entries))
        return {"status": "ignored", "reason": "no leads in New status"}

    log.info("Webhook: %d leads moved to New: %s", len(lead_ids), lead_ids)

    for lid in lead_ids:
        background_tasks.add_task(process_lead, lid)

    return {"status": "accepted", "leads": lead_ids}


@app.post("/webhook/nick-sync")
async def webhook_nick_sync(request: Request, background_tasks: BackgroundTasks):
    """
    Sync NICK field from lead to TelegramUsername_WZ on contact.

    Triggered by: lead status change (configured in amoCRM).
    If lead has NICK (@username) but linked contact's TelegramUsername_WZ
    is empty — copies NICK value to contact field. Prevents WhatsApp
    duplicates when Wazzup dedup checks TelegramUsername_WZ.

    amoCRM sends POST with form-encoded data like:
      leads[status][0][id]=12345
      leads[status][0][status_id]=60971918
    """
    try:
        form = await request.form()
        data = dict(form)
    except Exception:
        body = await request.body()
        log.debug("nick-sync raw body: %s", body[:500])
        data = {}

    # Parse lead IDs from status change events (same format as /webhook)
    lead_entries = {}
    for key, value in data.items():
        if not key.startswith("leads[status]"):
            continue
        parts = key.replace("leads[status][", "").rstrip("]").split("][")
        if len(parts) == 2:
            idx, field = parts
            lead_entries.setdefault(idx, {})[field] = value

    lead_ids = []
    for idx, entry in lead_entries.items():
        try:
            lid = int(entry.get("id", 0))
        except (ValueError, TypeError):
            continue
        if lid:
            lead_ids.append(lid)

    if not lead_ids:
        log.debug("nick-sync: no lead IDs found (entries: %d)", len(lead_entries))
        return {"status": "ignored", "reason": "no lead IDs"}

    log.info("nick-sync: %d leads to process: %s", len(lead_ids), lead_ids)

    for lid in lead_ids:
        background_tasks.add_task(process_nick_sync, lid)

    return {"status": "accepted", "leads": lead_ids}


def process_nick_sync(lead_id: int):
    """Copy NICK from lead to TelegramUsername_WZ on linked contact."""
    try:
        # 1. Get lead with contacts
        lead = crm.get_lead(lead_id, with_contacts=True)
        if not lead:
            log.warning("nick-sync lead %d: cannot fetch lead", lead_id)
            return

        # 2. Extract NICK field
        nick_raw = extract_field(lead, LEAD_NICK_FIELD_ID)
        if not nick_raw or not nick_raw.strip():
            log.debug("nick-sync lead %d: NICK empty", lead_id)
            return

        # Normalize: strip whitespace, remove leading @, then re-add @
        nick = nick_raw.strip().lstrip("@").strip()
        if not nick:
            log.debug("nick-sync lead %d: NICK is only whitespace/@: '%s'", lead_id, nick_raw)
            return
        nick = "@" + nick

        # 3. Get linked contact
        contacts = (lead.get("_embedded") or {}).get("contacts") or []
        if not contacts:
            log.debug("nick-sync lead %d: no linked contacts", lead_id)
            return

        contact_id = contacts[0]["id"]
        contact = crm.get_contact(contact_id)
        if not contact:
            log.warning("nick-sync lead %d: cannot fetch contact %d", lead_id, contact_id)
            return

        # 4. Check if TelegramUsername_WZ already filled
        existing_wz = extract_field(contact, CONTACT_TG_USERNAME_WZ)
        if existing_wz:
            log.debug(
                "nick-sync lead %d: contact %d already has TelegramUsername_WZ=%s, skipping",
                lead_id, contact_id, existing_wz,
            )
            return

        # 5. Copy NICK → TelegramUsername_WZ
        result = crm.patch("/contacts", [{
            "id": contact_id,
            "custom_fields_values": [{
                "field_id": CONTACT_TG_USERNAME_WZ,
                "values": [{"value": nick}],
            }],
        }])

        if result is not None:
            log.info(
                "nick-sync lead %d: SYNCED %s → contact %d TelegramUsername_WZ",
                lead_id, nick, contact_id,
            )
        else:
            log.error("nick-sync lead %d: FAILED to patch contact %d", lead_id, contact_id)

    except Exception as e:
        log.error("nick-sync lead %d: error: %s", lead_id, e, exc_info=True)


async def process_lead(lead_id: int):
    """Process a single lead for deduplication."""
    try:
        log.info("Processing lead %d...", lead_id)
        result = engine.check_and_merge(lead_id)

        action = result.get("action", "none")
        if action == "merge":
            log.info(
                "MERGED lead %d: old_contact=%s, new_contact=%s, login=@%s, steps=%s",
                lead_id,
                result.get("old_contact_id"),
                result.get("new_contact_id"),
                result.get("login"),
                result.get("steps"),
            )
        elif action == "no_match":
            log.info("Lead %d: Umnico contact @%s — no existing match", lead_id, result.get("login"))
        elif action == "none":
            log.debug("Lead %d: not an Umnico contact, skipping", lead_id)
        else:
            log.info("Lead %d: action=%s", lead_id, action)

    except Exception as e:
        log.error("Error processing lead %d: %s", lead_id, e, exc_info=True)


if __name__ == "__main__":
    uvicorn.run(app, host=SERVICE_HOST, port=SERVICE_PORT)
