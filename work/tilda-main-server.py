"""
Tilda Referral Webhook -> amoCRM Note Service

Receives "Приведи друга" form submissions from Tilda,
finds the matching deal in amoCRM by sender's phone,
and adds all form fields as a note to the deal.
"""

import os
import asyncio
import logging
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

# ── Tilda field mapping ──
# Actual field names from Tilda form "sarafan_all":
#   name     = ФИО друга
#   phone    = Телефон друга
#   nick     = Telegram ID друга
#   rec      = ФИО отправителя (рекомендателя)
#   phone_2  = Телефон отправителя (для начисления бонусов)
#   Input    = Комментарий
#   tranid, formid, formname = служебные поля Тильды

FIELD_LABELS = {
    "name": "ФИО друга",
    "phone": "Телефон друга",
    "nick": "Telegram друга",
    "rec": "ФИО отправителя",
    "phone_2": "Телефон отправителя",
    "input": "Комментарий",
}

# Tilda service fields to skip
SKIP_FIELDS = {"tranid", "formid", "formname"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Tilda webhook service started on port %s", os.getenv("SERVICE_PORT", "8585"))
    yield
    log.info("Shutting down")


app = FastAPI(title="Tilda Referral Webhook", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "has_token": bool(crm.access_token)}


@app.post("/webhook/tilda-referral")
async def tilda_referral(request: Request, background_tasks: BackgroundTasks):
    """Receives form data from Tilda (application/x-www-form-urlencoded)."""
    content_type = request.headers.get("content-type", "")

    if "json" in content_type:
        payload = await request.json()
    else:
        form = await request.form()
        payload = dict(form)

    log.info("Tilda webhook received (%d fields) from form=%s",
             len(payload), payload.get("formname", "unknown"))
    for key, value in payload.items():
        log.info("  %s = %s", key, value)

    background_tasks.add_task(process_referral, payload)
    return {"status": "ok", "fields_received": len(payload)}


async def process_referral(payload: dict):
    """Find deal in amoCRM by sender's phone, add note with all form fields."""
    # Wait for Tilda's direct amoCRM integration to create the deal first
    await asyncio.sleep(7)

    # Build note text
    lines = ["Форма «Приведи друга»", ""]
    for key, value in payload.items():
        if not value or key.lower() in SKIP_FIELDS:
            continue
        label = FIELD_LABELS.get(key.lower(), key)
        lines.append(f"{label}: {value}")
    note_text = "\n".join(lines)

    # Find deal by sender's phone (phone_2 = телефон отправителя)
    phone = payload.get("phone_2") or payload.get("phone")
    if not phone:
        log.warning("No phone in payload, cannot find deal. Note:\n%s", note_text)
        return

    log.info("Searching contact by phone: %s", phone)
    contact = crm.find_contact_by_phone(phone)

    if not contact:
        log.warning("No contact found for phone %s", phone)
        return

    log.info("Found contact: id=%s, name=%s", contact["id"], contact.get("name"))

    # Get most recent lead
    leads = crm.get_contact_leads(contact["id"])
    if not leads:
        log.warning("Contact %s has no leads", contact["id"])
        return

    leads.sort(key=lambda x: x.get("id", 0), reverse=True)
    lead_id = leads[0]["id"]

    log.info("Adding note to lead %d", lead_id)
    result = crm.add_note_to_lead(lead_id, note_text)

    if result:
        log.info("Note added successfully to lead %d", lead_id)
    else:
        log.error("Failed to add note to lead %d", lead_id)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("SERVICE_PORT", "8585")))
