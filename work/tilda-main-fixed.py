"""
Tilda Referral Webhook -> amoCRM Note Service

Two-endpoint architecture:
  1. POST /webhook/tilda-referral  — receives ALL form fields from Tilda, caches by TRANID
  2. POST /webhook/sarafan         — receives lead ID from amoCRM trigger, writes note to THAT lead

Flow:
  Tilda form submit
    -> Tilda creates deal in amoCRM (partial fields)
    -> Tilda POSTs to /webhook/tilda-referral (all fields) -> cached
    -> amoCRM pipeline trigger (FORMNAME=sarafan_all) fires
    -> amoCRM POSTs to /webhook/sarafan with lead ID
    -> service fetches lead's TRANID, matches cached data, writes note
"""

import os
import time
import logging
from collections import OrderedDict
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request, BackgroundTasks
import uvicorn

from amocrm import AmoCRM

load_dotenv()

# ── Logging ──
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("tilda-webhook")

# ── amoCRM client ──
crm = AmoCRM(
    domain=os.getenv("AMOCRM_DOMAIN"),
    client_id=os.getenv("AMOCRM_CLIENT_ID"),
    client_secret=os.getenv("AMOCRM_CLIENT_SECRET"),
    redirect_uri=os.getenv("AMOCRM_REDIRECT_URI"),
)

# ── Form data cache (TRANID -> payload, max 500 entries, TTL 1 hour) ──
CACHE_MAX = 500
CACHE_TTL = 3600  # seconds

form_cache: OrderedDict[str, dict] = OrderedDict()


def cache_put(tranid: str, payload: dict):
    """Store form payload in cache, evict old entries."""
    now = time.time()
    form_cache[tranid] = {"payload": payload, "ts": now}
    # Evict expired or overflow
    while len(form_cache) > CACHE_MAX:
        form_cache.popitem(last=False)
    # Evict expired
    expired = [k for k, v in form_cache.items() if now - v["ts"] > CACHE_TTL]
    for k in expired:
        del form_cache[k]
    log.info("Cache: stored tranid=%s, size=%d", tranid, len(form_cache))


def cache_get(tranid: str) -> dict | None:
    """Get cached form payload by TRANID."""
    entry = form_cache.get(tranid)
    if not entry:
        return None
    if time.time() - entry["ts"] > CACHE_TTL:
        del form_cache[tranid]
        return None
    return entry["payload"]


# ── Tilda field mapping ──
FIELD_LABELS = {
    "name": "ФИО друга",
    "phone": "Телефон друга",
    "nick": "Telegram друга",
    "rec": "ФИО отправителя",
    "phone_2": "Телефон отправителя",
    "input": "Комментарий",
}

SKIP_FIELDS = {"tranid", "formid", "formname"}

# amoCRM field IDs
TRANID_FIELD_ID = 1428405
FORMNAME_FIELD_ID = 1364107


def extract_field(entity: dict, field_id: int) -> str | None:
    """Extract custom field value from an amoCRM entity."""
    for cf in entity.get("custom_fields_values") or []:
        if cf["field_id"] == field_id:
            vals = cf.get("values", [])
            if vals:
                return str(vals[0].get("value", "")).strip()
    return None


def build_note_text(payload: dict) -> str:
    """Build note text from form payload."""
    lines = ["Форма «Приведи друга»", ""]
    for key, value in payload.items():
        if not value or key.lower() in SKIP_FIELDS:
            continue
        label = FIELD_LABELS.get(key.lower(), key)
        lines.append(f"{label}: {value}")
    return "\n".join(lines)


# ── FastAPI app ──

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Tilda webhook service started on port %s", os.getenv("SERVICE_PORT", "8585"))
    yield
    log.info("Shutting down")


app = FastAPI(title="Tilda Referral Webhook", lifespan=lifespan)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "has_token": bool(crm.access_token),
        "cache_size": len(form_cache),
    }


@app.post("/webhook/tilda-referral")
async def tilda_referral(request: Request):
    """
    Endpoint 1: receives ALL form fields from Tilda.
    Caches them by TRANID for later matching with amoCRM webhook.
    """
    content_type = request.headers.get("content-type", "")
    if "json" in content_type:
        payload = await request.json()
    else:
        form = await request.form()
        payload = dict(form)

    log.info("Tilda form received (%d fields) from form=%s",
             len(payload), payload.get("formname", "unknown"))
    for key, value in payload.items():
        log.info("  %s = %s", key, value)

    # Cache by TRANID
    tranid = payload.get("tranid", "")
    if tranid:
        cache_put(tranid, payload)
    else:
        log.warning("No TRANID in payload, cannot cache")

    return {"status": "cached", "tranid": tranid, "fields_received": len(payload)}


@app.post("/webhook/sarafan")
async def sarafan_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint 2: receives lead ID from amoCRM pipeline trigger.
    Trigger condition: FORMNAME = sarafan_all.
    amoCRM sends form-encoded: leads[status][0][id]=12345
    """
    try:
        form = await request.form()
        data = dict(form)
    except Exception:
        body = await request.body()
        log.info("Raw body: %s", body[:500])
        data = {}

    log.info("amoCRM webhook received (%d fields)", len(data))

    # Parse lead IDs from amoCRM webhook
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

    lead_ids = list(dict.fromkeys(lead_ids))

    if not lead_ids:
        log.info("No lead IDs in amoCRM webhook")
        return {"status": "ignored", "reason": "no lead IDs"}

    log.info("Processing %d leads from amoCRM trigger: %s", len(lead_ids), lead_ids)

    for lid in lead_ids:
        background_tasks.add_task(process_sarafan_note, lid)

    return {"status": "accepted", "leads": lead_ids}


def process_sarafan_note(lead_id: int):
    """Fetch lead's TRANID, match cached form data, add note + tag + rename."""
    try:
        # 1. Fetch lead from amoCRM
        lead = crm.get(f"/leads/{lead_id}")
        if not lead:
            log.warning("Lead %d: cannot fetch from amoCRM", lead_id)
            return

        # 2. Verify FORMNAME = sarafan_all
        formname = extract_field(lead, FORMNAME_FIELD_ID)
        if formname != "sarafan_all":
            log.info("Lead %d: FORMNAME=%s, not sarafan_all, skipping", lead_id, formname)
            return

        # 3. Get TRANID and look up cached form data
        tranid = extract_field(lead, TRANID_FIELD_ID)
        if not tranid:
            log.warning("Lead %d: no TRANID field, cannot match form data", lead_id)
            return

        log.info("Lead %d: TRANID=%s, looking up cached form data", lead_id, tranid)
        payload = cache_get(tranid)

        if payload:
            note_text = build_note_text(payload)
            rec_name = payload.get("rec", "").strip()
            log.info("Lead %d: matched cached form data, rec=%s", lead_id, rec_name)
        else:
            # Fallback: build note from amoCRM fields only
            log.warning("Lead %d: no cached form data for TRANID=%s, using amoCRM fields",
                        lead_id, tranid)
            nick = extract_field(lead, 1612133) or ""
            rec_name = ""
            note_text = (
                "Форма «Приведи друга»\n\n"
                f"NICK: {nick}\n"
                f"TRANID: {tranid}\n"
                "(Подробные данные формы недоступны — Tilda webhook не получен)"
            )

        # 4. Add note to THIS lead
        log.info("Lead %d: adding note", lead_id)
        result = crm.add_note_to_lead(lead_id, note_text)
        if result:
            log.info("Lead %d: note added successfully", lead_id)
        else:
            log.error("Lead %d: failed to add note", lead_id)

        # 5. Add tag "Сарафан" to the lead
        log.info("Lead %d: adding tag 'Сарафан'", lead_id)
        tag_result = crm.patch("/leads", [{
            "id": lead_id,
            "_embedded": {
                "tags": [{"name": "Сарафан"}]
            }
        }])
        if tag_result:
            log.info("Lead %d: tag 'Сарафан' added", lead_id)
        else:
            log.error("Lead %d: failed to add tag", lead_id)

        # 6. Rename lead to "Сарафан от {rec}"
        if rec_name:
            new_name = f"Сарафан от {rec_name}"
        else:
            new_name = "Сарафан"
        log.info("Lead %d: renaming to '%s'", lead_id, new_name)
        rename_result = crm.patch("/leads", [{
            "id": lead_id,
            "name": new_name,
        }])
        if rename_result:
            log.info("Lead %d: renamed to '%s'", lead_id, new_name)
        else:
            log.error("Lead %d: failed to rename", lead_id)

    except Exception as e:
        log.error("Lead %d: %s", lead_id, e, exc_info=True)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("SERVICE_PORT", "8585")))
