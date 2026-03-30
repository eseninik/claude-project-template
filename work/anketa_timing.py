"""
Fetch all amoCRM leads with "анкета заполнена" = Да,
find the "анкета предварительной квалификации" note for each,
compare lead creation time vs note creation time,
split into <30min / >=30min sheets in Google Sheets.
"""

import json
import time
import logging
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# ── Config ──
AMOCRM_DOMAIN = "migratoramocrm.amocrm.ru"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjQ5ZjE2ZmIzMzlmZjMzZjU2ZTk5M2VkM2I5ZGE4NmFiMjFjYjdjYzBkNDE4MDMzNzk4Mjc3YjAyZGU2NzRmNGMwOTY2OGMxNGU3NWM1MWMwIn0.eyJhdWQiOiJmNjg2Mzc3Yi0wOWQ2LTQwZmYtYTVjOS1jNDcyMzRjOTA2ODEiLCJqdGkiOiI0OWYxNmZiMzM5ZmYzM2Y1NmU5OTNlZDNiOWRhODZhYjIxY2I3Y2MwZDQxODAzMzc5ODI3N2IwMmRlNjc0ZjRjMDk2NjhjMTRlNzVjNTFjMCIsImlhdCI6MTc2ODMzMjgzOSwibmJmIjoxNzY4MzMyODM5LCJleHAiOjE5MjYwMjg4MDAsInN1YiI6IjEyNDM2NzM0IiwiZ3JhbnRfdHlwZSI6IiIsImFjY291bnRfaWQiOjMxMzMyNTk0LCJiYXNlX2RvbWFpbiI6ImFtb2NybS5ydSIsInZlcnNpb24iOjIsInNjb3BlcyI6WyJjcm0iLCJmaWxlcyIsImZpbGVzX2RlbGV0ZSIsIm5vdGlmaWNhdGlvbnMiLCJwdXNoX25vdGlmaWNhdGlvbnMiXSwiaGFzaF91dWlkIjoiYTA5OTZlOTctODY5OS00NzNjLTg0MzEtMTZmMWU5YmM2ODMwIiwidXNlcl9mbGFncyI6MCwiYXBpX2RvbWFpbiI6ImFwaS1iLmFtb2NybS5ydSJ9.nQ6Zdb6eRAaWcmes0vDozHiufbMgj2B4GgiMfxTsRejBRS-54EAPLGiXYGTr4rP1nN9dxLmjEyLJib9BXVePnCFVpZxftAOhS_bOcI4Cm1Y69sw3ba_qvYScYuV7F28ykFVii1PAR4Q0ADUKO9NEAMvekRtDYHzuIwc157gAga2JKMtCyp_5CdOTQIkru3GDcboZl9LRaSaPzXyI6C7h9F7l2ynU8uCTBKOxok1iIZJHOg6bt3a-mkSeu6o2ryubdIlXiMFlVsgSvVDmuVGMGmJVeJ2bfgo5kCiVRQaRHJTji8R0BJpaNUPuNdttDZ7072q3f8W9y6rhqhyNXM412g"
BASE_URL = f"https://{AMOCRM_DOMAIN}/api/v4"
SPREADSHEET_ID = "1o7a46ZjjS9fmcfx49dvQeOPzkUBe8_7dFcThtM2Xy1A"
CREDENTIALS_FILE = str(Path(__file__).parent.parent / "credentials.json")
ANKETA_FIELD_ID = 1655029       # "Анкета заполнена"
ANKETA_DATE_FIELD_ID = 1655031  # "Дата заполнения анкеты"
SEARCH_TEXT = "анкета предварительной квалификации"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

MOSCOW = timedelta(hours=3)


# ── amoCRM API ──

def amo_get(path: str, params: dict = None) -> dict | None:
    """GET request to amoCRM API with rate limiting."""
    url = f"{BASE_URL}{path}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
        if query:
            url += f"?{query}"

    req = Request(url, headers={
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    })

    try:
        with urlopen(req) as resp:
            raw = resp.read().decode()
            time.sleep(0.2)
            if not raw.strip():
                return {}
            return json.loads(raw)
    except HTTPError as e:
        if e.code == 429:
            log.warning("Rate limited, waiting 5s...")
            time.sleep(5)
            return amo_get(path, params)
        if e.code == 204:
            return {}
        body = e.read().decode()[:300]
        log.error("API GET %s -> %s: %s", path, e.code, body)
        return None


def fetch_all_leads() -> list[dict]:
    """Fetch ALL leads, paginated."""
    all_leads = []
    page = 1
    while True:
        log.info("Fetching leads page %d (total so far: %d)...", page, len(all_leads))
        data = amo_get("/leads", {"page": str(page), "limit": "250"})
        if not data or "_embedded" not in data:
            break
        batch = data["_embedded"]["leads"]
        all_leads.extend(batch)
        if "next" not in data.get("_links", {}):
            break
        page += 1
    return all_leads


def fetch_lead_notes(lead_id: int) -> list[dict]:
    """Fetch notes for a specific lead."""
    data = amo_get(f"/leads/{lead_id}/notes", {"limit": "250"})
    if data and "_embedded" in data:
        return data["_embedded"]["notes"]
    return []


def get_custom_field(lead: dict, field_id: int) -> str:
    """Get custom field value by field_id."""
    for cf in lead.get("custom_fields_values") or []:
        if cf.get("field_id") == field_id:
            vals = cf.get("values", [])
            if vals:
                return str(vals[0].get("value", ""))
    return ""


def get_custom_field_by_code(lead: dict, field_code: str) -> str:
    """Get custom field value by code."""
    for cf in lead.get("custom_fields_values") or []:
        if cf.get("field_code") == field_code:
            vals = cf.get("values", [])
            if vals:
                return str(vals[0].get("value", ""))
    return ""


def ts_to_moscow(ts: int) -> str:
    """Unix timestamp to Moscow time string."""
    dt = datetime.fromtimestamp(ts, tz=timezone.utc) + MOSCOW
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# ── Main ──

def main():
    log.info("=== Anketa Timing Analysis ===")

    # Step 1: Fetch all leads
    log.info("Step 1: Fetching all leads...")
    all_leads = fetch_all_leads()
    log.info("Total leads: %d", len(all_leads))

    # Step 2: Filter leads with anketa filled
    anketa_leads = []
    for lead in all_leads:
        val = get_custom_field(lead, ANKETA_FIELD_ID)
        if val:
            anketa_leads.append(lead)

    log.info("Leads with anketa filled: %d", len(anketa_leads))

    if not anketa_leads:
        log.warning("No leads with anketa. Exiting.")
        return

    # Step 3: For each anketa lead, find the anketa note
    under_30 = []
    over_30 = []
    no_note = []

    for i, lead in enumerate(anketa_leads):
        lead_id = lead["id"]
        log.info("Processing %d/%d: lead %d...", i + 1, len(anketa_leads), lead_id)

        notes = fetch_lead_notes(lead_id)

        # Find the anketa note
        anketa_note = None
        for note in notes:
            text = (note.get("params") or {}).get("text", "")
            if SEARCH_TEXT.lower() in text.lower():
                if anketa_note is None or note["created_at"] < anketa_note["created_at"]:
                    anketa_note = note

        lead_created = lead.get("created_at", 0)
        anketa_date_field = get_custom_field(lead, ANKETA_DATE_FIELD_ID)

        if anketa_note is None:
            log.warning("  Lead %d has anketa=Да but no anketa note found!", lead_id)
            no_note.append({
                "lead_id": lead_id,
                "lead_name": lead.get("name", ""),
                "nick": get_custom_field_by_code(lead, "NICK"),
                "lead_created_str": ts_to_moscow(lead_created),
                "note_created_str": "НЕТ ПРИМЕЧАНИЯ",
                "delta_min": "N/A",
                "anketa_date_field": anketa_date_field,
                "pipeline_id": lead.get("pipeline_id", ""),
                "status_id": lead.get("status_id", ""),
                "responsible_user_id": lead.get("responsible_user_id", ""),
                "link": f"https://migratoramocrm.amocrm.ru/leads/detail/{lead_id}",
            })
            continue

        note_created = anketa_note["created_at"]
        delta_sec = note_created - lead_created
        delta_min = round(delta_sec / 60.0, 1)

        row = {
            "lead_id": lead_id,
            "lead_name": lead.get("name", ""),
            "nick": get_custom_field_by_code(lead, "NICK"),
            "lead_created_str": ts_to_moscow(lead_created),
            "note_created_str": ts_to_moscow(note_created),
            "delta_min": delta_min,
            "anketa_date_field": anketa_date_field,
            "pipeline_id": lead.get("pipeline_id", ""),
            "status_id": lead.get("status_id", ""),
            "responsible_user_id": lead.get("responsible_user_id", ""),
            "link": f"https://migratoramocrm.amocrm.ru/leads/detail/{lead_id}",
        }

        if delta_min < 30:
            under_30.append(row)
        else:
            over_30.append(row)

    log.info("Results: <30min=%d, >=30min=%d, no_note=%d", len(under_30), len(over_30), len(no_note))

    # Sort by delta
    under_30.sort(key=lambda r: r["delta_min"])
    over_30.sort(key=lambda r: r["delta_min"])

    # Step 4: Write to Google Sheets
    log.info("Step 4: Writing to Google Sheets...")
    write_to_sheets(under_30, over_30, no_note)
    log.info("=== Done ===")


def write_to_sheets(under_30: list, over_30: list, no_note: list):
    """Write results to Google Sheets."""
    creds = Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    service = build("sheets", "v4", credentials=creds)
    sheets = service.spreadsheets()

    # Get existing sheet names
    meta = sheets.get(spreadsheetId=SPREADSHEET_ID).execute()
    existing_sheets = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}

    # Create needed sheets
    needed = ["Менее 30 мин", "Более 30 мин", "Без примечания"]
    requests = []
    for title in needed:
        if title not in existing_sheets:
            requests.append({"addSheet": {"properties": {"title": title}}})

    if requests:
        sheets.batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"requests": requests},
        ).execute()
        log.info("Created %d new sheet tabs", len(requests))

    # Clear existing data in all sheets
    for title in needed:
        try:
            sheets.values().clear(
                spreadsheetId=SPREADSHEET_ID,
                range=f"'{title}'!A:Z",
            ).execute()
        except Exception:
            pass

    header = [
        "ID сделки", "Имя", "NICK",
        "Сделка создана (МСК)", "Анкета-примечание создано (МСК)",
        "Разница (мин)", "Дата анкеты (поле)",
        "Pipeline ID", "Status ID", "Ответственный", "Ссылка"
    ]

    def rows_to_values(rows_list):
        values = [header]
        for r in rows_list:
            values.append([
                r["lead_id"], r["lead_name"], r["nick"],
                r["lead_created_str"], r["note_created_str"],
                r["delta_min"], r["anketa_date_field"],
                r["pipeline_id"], r["status_id"],
                r["responsible_user_id"], r["link"],
            ])
        return values

    # Write each sheet
    for title, data_list in [
        ("Менее 30 мин", under_30),
        ("Более 30 мин", over_30),
        ("Без примечания", no_note),
    ]:
        vals = rows_to_values(data_list)
        sheets.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{title}'!A1",
            valueInputOption="RAW",
            body={"values": vals},
        ).execute()
        log.info("Written %d rows to '%s'", len(data_list), title)

    log.info("Spreadsheet: https://docs.google.com/spreadsheets/d/%s", SPREADSHEET_ID)


if __name__ == "__main__":
    main()
