"""
Re-sync NICK -> TelegramUsername_WZ for leads created after 2026-03-17.

Finds leads with NICK field filled where the linked contact
has empty TelegramUsername_WZ, and syncs the value.
Also detects potential duplicates.

Usage:
    py -3 work/nick_resync.py              # dry-run (report only)
    py -3 work/nick_resync.py --execute    # actually patch contacts
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path

import aiohttp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("nick_resync")

# ── Config ───────────────────────────────────────────────────────────────────
AMOCRM_DOMAIN = "migratoramocrm.amocrm.ru"
AMOCRM_BASE_URL = f"https://{AMOCRM_DOMAIN}/api/v4"
TOKEN_FILE = Path("work/amo_tokens.json")

NICK_FIELD_ID = 1612133
TG_USERNAME_WZ_FIELD_ID = 1648299

# March 17 2026 00:00 UTC
CREATED_AFTER = 1773964800

MAX_CONCURRENT = 5
EXECUTE = "--execute" in sys.argv


def load_token() -> str:
    data = json.loads(TOKEN_FILE.read_text())
    return data["access_token"]


def extract_field(entity: dict, field_id: int) -> str:
    for cf in entity.get("custom_fields_values") or []:
        if cf["field_id"] == field_id:
            vals = cf.get("values", [])
            if vals:
                return str(vals[0].get("value", "")).strip()
    return ""


async def fetch_all_leads(session: aiohttp.ClientSession, token: str) -> list:
    """Fetch all leads created after CREATED_AFTER with pagination."""
    all_leads = []
    page = 1
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    while True:
        params = {
            "limit": "250",
            "page": str(page),
            "with": "contacts",
            "filter[created_at][from]": str(CREATED_AFTER),
            "order[created_at]": "desc",
        }
        url = f"{AMOCRM_BASE_URL}/leads"
        async with session.get(url, headers=headers, params=params) as resp:
            if resp.status == 204:
                break
            if resp.status != 200:
                body = await resp.text()
                log.error("Fetch leads page %d: %s %s", page, resp.status, body[:200])
                break
            data = await resp.json()

        leads = data.get("_embedded", {}).get("leads", [])
        if not leads:
            break

        all_leads.extend(leads)
        log.info("Fetched page %d: %d leads (total: %d)", page, len(leads), len(all_leads))

        if "next" not in data.get("_links", {}):
            break
        page += 1
        await asyncio.sleep(0.2)

    return all_leads


async def fetch_contact(session: aiohttp.ClientSession, token: str,
                        contact_id: int, sem: asyncio.Semaphore) -> dict | None:
    async with sem:
        await asyncio.sleep(0.15)
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{AMOCRM_BASE_URL}/contacts/{contact_id}"
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return None
            return await resp.json()


async def patch_contact_wz(session: aiohttp.ClientSession, token: str,
                           contact_id: int, nick: str, sem: asyncio.Semaphore) -> bool:
    async with sem:
        await asyncio.sleep(0.15)
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        url = f"{AMOCRM_BASE_URL}/contacts"
        data = [{
            "id": contact_id,
            "custom_fields_values": [{
                "field_id": TG_USERNAME_WZ_FIELD_ID,
                "values": [{"value": nick}],
            }]
        }]
        async with session.patch(url, headers=headers, json=data) as resp:
            return resp.status == 200


async def main():
    log.info("=== NICK Re-sync (created after 2026-03-17) ===")
    log.info("Mode: %s", "EXECUTE" if EXECUTE else "DRY-RUN")
    start = time.time()

    token = load_token()

    async with aiohttp.ClientSession() as session:
        # Step 1: Fetch all leads after March 17
        leads = await fetch_all_leads(session, token)
        log.info("Total leads after 2026-03-17: %d", len(leads))

        # Step 2: Filter leads with NICK field
        leads_with_nick = []
        for lead in leads:
            nick = extract_field(lead, NICK_FIELD_ID)
            if nick:
                contacts = (lead.get("_embedded") or {}).get("contacts", [])
                if contacts:
                    leads_with_nick.append({
                        "lead_id": lead["id"],
                        "lead_name": lead.get("name", ""),
                        "nick": nick,
                        "contact_id": contacts[0]["id"],
                        "created_at": lead.get("created_at", 0),
                    })

        log.info("Leads with NICK filled: %d", len(leads_with_nick))

        # Step 3: Check which contacts have empty TelegramUsername_WZ
        sem = asyncio.Semaphore(MAX_CONCURRENT)
        needs_sync = []
        already_synced = []

        # Batch fetch contacts
        contact_ids = list(set(l["contact_id"] for l in leads_with_nick))
        log.info("Unique contacts to check: %d", len(contact_ids))

        contact_cache = {}
        for i in range(0, len(contact_ids), 50):
            batch = contact_ids[i:i+50]
            tasks = [fetch_contact(session, token, cid, sem) for cid in batch]
            results = await asyncio.gather(*tasks)
            for cid, result in zip(batch, results):
                if result:
                    contact_cache[cid] = result
            log.info("Fetched contacts: %d/%d", min(i+50, len(contact_ids)), len(contact_ids))

        # Classify
        for item in leads_with_nick:
            contact = contact_cache.get(item["contact_id"])
            if not contact:
                continue
            existing_wz = extract_field(contact, TG_USERNAME_WZ_FIELD_ID)
            item["existing_wz"] = existing_wz
            item["contact_name"] = contact.get("name", "")

            if not existing_wz:
                needs_sync.append(item)
            else:
                already_synced.append(item)

        log.info("")
        log.info("=== RESULTS ===")
        log.info("Already synced (WZ filled): %d", len(already_synced))
        log.info("NEEDS sync (WZ empty): %d", len(needs_sync))

        # Step 4: Find duplicates (same nick, different contacts)
        nick_to_contacts = {}
        for item in leads_with_nick:
            nick_norm = item["nick"].lower().lstrip("@").strip()
            if nick_norm not in nick_to_contacts:
                nick_to_contacts[nick_norm] = []
            nick_to_contacts[nick_norm].append(item)

        duplicates = {k: v for k, v in nick_to_contacts.items() if len(v) > 1}
        if duplicates:
            log.info("")
            log.info("=== POTENTIAL DUPLICATES (same nick, multiple leads) ===")
            for nick, items in duplicates.items():
                contact_ids_set = set(i["contact_id"] for i in items)
                if len(contact_ids_set) > 1:  # Different contacts = real duplicate
                    log.info("@%s -> %d leads, %d contacts (DIFFERENT CONTACTS):", nick, len(items), len(contact_ids_set))
                    for i in items:
                        log.info("  Lead %d (%s) -> Contact %d (%s) WZ=%s",
                                 i["lead_id"], i["lead_name"], i["contact_id"],
                                 i.get("contact_name", "?"), i.get("existing_wz", "?"))

        # Step 5: Sync if --execute
        if EXECUTE and needs_sync:
            log.info("")
            log.info("=== EXECUTING SYNC ===")
            synced = 0
            for item in needs_sync:
                nick = item["nick"].strip()
                if not nick.startswith("@"):
                    nick = "@" + nick
                success = await patch_contact_wz(session, token, item["contact_id"], nick, sem)
                if success:
                    synced += 1
                    log.info("SYNCED: Lead %d -> Contact %d: %s",
                             item["lead_id"], item["contact_id"], nick)
                else:
                    log.error("FAILED: Lead %d -> Contact %d", item["lead_id"], item["contact_id"])
            log.info("Synced: %d/%d", synced, len(needs_sync))
        elif needs_sync:
            log.info("")
            log.info("=== NEEDS SYNC (dry-run, use --execute to apply) ===")
            for item in needs_sync:
                log.info("  Lead %d (%s) -> Contact %d (%s): NICK=%s, WZ=empty",
                         item["lead_id"], item["lead_name"], item["contact_id"],
                         item.get("contact_name", "?"), item["nick"])

    elapsed = time.time() - start
    log.info("")
    log.info("Done in %.1f seconds", elapsed)

    # Save report
    report = {
        "total_leads": len(leads),
        "leads_with_nick": len(leads_with_nick),
        "needs_sync": len(needs_sync),
        "already_synced": len(already_synced),
        "duplicates": len(duplicates),
        "needs_sync_details": needs_sync,
        "duplicate_details": {k: [{"lead_id": i["lead_id"], "contact_id": i["contact_id"],
                                    "lead_name": i["lead_name"]}
                                   for i in v]
                              for k, v in duplicates.items()
                              if len(set(i["contact_id"] for i in v)) > 1},
    }
    Path("work/nick_resync_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Report saved to work/nick_resync_report.json")


if __name__ == "__main__":
    asyncio.run(main())
