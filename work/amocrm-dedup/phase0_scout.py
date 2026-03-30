"""
Phase 0: AmoCRM Duplicate Scout — READ ONLY
Finds duplicate contacts by matching Telegram username.

Old deals have NICK field (@username).
New contacts from Umnico have "Логин" field (username without @).

This script ONLY READS data and generates a report. No changes to CRM.

Usage:
    python phase0_scout.py --token YOUR_TOKEN
    python phase0_scout.py --token YOUR_TOKEN --output report.csv
"""

import argparse
import csv
import json
import time
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from datetime import datetime

AMOCRM_DOMAIN = "migratoramocrm.amocrm.ru"
BASE_URL = f"https://{AMOCRM_DOMAIN}/api/v4"

# Known field IDs (leads)
LEAD_NICK_FIELD_ID = 1612133  # NICK field on leads — contains @username

# Known contact field IDs (fallback if auto-detect fails)
KNOWN_CONTACT_FIELDS = {
    130527: "telegram_id",
    1648299: "telegram_username",
    1648301: "telegram_id_wz",
    1654991: "umnico_social_id",
    1654993: "umnico_customer_id",
    1655001: "login",  # Логин field
}

# These will be auto-detected from contacts custom fields
CONTACT_FIELD_IDS = {}  # Filled at runtime


def _has_next_page(data: dict) -> bool:
    """Check if amoCRM response has a next page via _links.next."""
    links = data.get("_links", {})
    return "next" in links


def api_get(path: str, token: str, params: dict = None) -> dict | list | None:
    """Make GET request to amoCRM API with rate limiting."""
    url = f"{BASE_URL}{path}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
        if query:
            url += f"?{query}"

    req = Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })

    try:
        with urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            time.sleep(0.15)  # Rate limit: ~7 req/sec
            return data
    except HTTPError as e:
        if e.code == 204:  # No content
            return None
        if e.code == 429:  # Rate limited
            print("  [!] Rate limited, waiting 2s...")
            time.sleep(2)
            return api_get(path, token, params)
        print(f"  [!] API Error {e.code}: {e.read().decode()[:200]}")
        return None


def detect_contact_fields(token: str) -> dict:
    """Auto-detect relevant custom field IDs on contacts."""
    print("[1/5] Detecting contact custom fields...")
    fields = {}
    page = 1

    while True:
        data = api_get("/contacts/custom_fields", token, {"page": page, "limit": 250})
        if not data or "_embedded" not in data:
            break

        for field in data["_embedded"]["custom_fields"]:
            name_lower = field["name"].lower()
            fid = field["id"]

            # First: check by known field ID (reliable)
            if fid in KNOWN_CONTACT_FIELDS:
                key = KNOWN_CONTACT_FIELDS[fid]
                fields[key] = fid
                print(f"  Found (by ID): {field['name']} -> field {fid} ({key})")
                continue

            # Fallback: detect by name pattern
            if "umnico" in name_lower and "social" in name_lower:
                fields["umnico_social_id"] = fid
                print(f"  Found: Umnico socialId -> field {fid}")
            elif "umnico" in name_lower and "customer" in name_lower:
                fields["umnico_customer_id"] = fid
                print(f"  Found: Umnico customerId -> field {fid}")
            elif fid not in fields.values() and name_lower in ("логин", "login"):
                fields["login"] = fid
                print(f"  Found: Логин -> field {fid}")
            elif name_lower == "telegram id":
                fields["telegram_id"] = fid
                print(f"  Found: Telegram ID -> field {fid}")
            elif "telegramusername" in name_lower.replace("_", "").replace(" ", ""):
                fields["telegram_username"] = fid
                print(f"  Found: TelegramUsername -> field {fid}")
            elif "telegramid_wz" in name_lower.replace(" ", ""):
                fields["telegram_id_wz"] = fid
                print(f"  Found: TelegramId_WZ -> field {fid}")

        if not _has_next_page(data):
            break
        page += 1

    if not fields:
        print("  [!] Warning: No relevant contact fields detected!")
    else:
        print(f"  Total fields detected: {len(fields)}")
    return fields


def get_all_contacts(token: str) -> list:
    """Fetch all contacts with custom fields."""
    print("[2/5] Fetching all contacts...")
    contacts = []
    page = 1

    while True:
        data = api_get("/contacts", token, {
            "page": page,
            "limit": 250,
            "with": "leads",
        })
        if not data or "_embedded" not in data:
            break

        batch = data["_embedded"]["contacts"]
        contacts.extend(batch)
        print(f"  Page {page}: {len(batch)} contacts (total: {len(contacts)})")

        if not _has_next_page(data):
            break
        page += 1

    return contacts


def get_all_leads_with_nick(token: str) -> dict:
    """Fetch all leads and filter for NICK field. Returns {lead_id: nick_value}."""
    print("[3/5] Fetching all leads (scanning for NICK field)...")
    leads_nick = {}
    page = 1

    while True:
        data = api_get("/leads", token, {
            "page": page,
            "limit": 250,
            "with": "contacts",
        })
        if not data or "_embedded" not in data:
            break

        for lead in data["_embedded"]["leads"]:
            nick = _extract_field(lead, LEAD_NICK_FIELD_ID)
            if nick:
                leads_nick[lead["id"]] = {
                    "nick": nick,
                    "name": lead.get("name", ""),
                    "contact_ids": _get_contact_ids(lead),
                }

        batch_size = len(data["_embedded"]["leads"])
        print(f"  Page {page}: {batch_size} leads (with NICK: {len(leads_nick)})")

        if not _has_next_page(data):
            break
        page += 1

    return leads_nick


def _extract_field(entity: dict, field_id: int) -> str | None:
    """Extract custom field value from entity."""
    for cf in entity.get("custom_fields_values") or []:
        if cf["field_id"] == field_id:
            values = cf.get("values", [])
            if values:
                return str(values[0].get("value", "")).strip()
    return None


def _get_contact_ids(lead: dict) -> list:
    """Extract contact IDs from lead's embedded contacts."""
    contacts = (lead.get("_embedded") or {}).get("contacts") or []
    return [c["id"] for c in contacts]


def normalize_username(raw: str) -> str:
    """Normalize Telegram username: strip @, lowercase, strip whitespace."""
    if not raw:
        return ""
    return raw.strip().lstrip("@").lower().strip()


def find_duplicates(contacts: list, leads_nick: dict, contact_fields: dict) -> list:
    """Find duplicate contacts by matching usernames."""
    print("[4/5] Analyzing duplicates...")

    # Build contact lookup
    contact_map = {}  # contact_id -> contact_data
    for c in contacts:
        contact_map[c["id"]] = c

    # Build username -> contact mapping from Umnico contacts (new)
    umnico_contacts = {}  # normalized_username -> contact

    social_id_field = contact_fields.get("umnico_social_id")
    login_field = contact_fields.get("login")

    print(f"  Using fields: umnico_social_id={social_id_field}, login={login_field}")

    umnico_count = 0
    login_count = 0

    for c in contacts:
        has_umnico = False
        umnico_social = None
        login_val = None

        for cf in c.get("custom_fields_values") or []:
            if social_id_field and cf["field_id"] == social_id_field:
                vals = cf.get("values", [])
                if vals:
                    umnico_social = str(vals[0].get("value", ""))
                    has_umnico = True
            if login_field and cf["field_id"] == login_field:
                vals = cf.get("values", [])
                if vals:
                    login_val = str(vals[0].get("value", ""))

        c["_umnico_social"] = umnico_social
        c["_login"] = login_val
        c["_has_umnico"] = has_umnico

        if has_umnico:
            umnico_count += 1
        if login_val:
            login_count += 1

        if has_umnico and login_val:
            normalized = normalize_username(login_val)
            if normalized:
                umnico_contacts[normalized] = c

    print(f"  Contacts with Umnico socialId: {umnico_count}")
    print(f"  Contacts with login field: {login_count}")
    print(f"  Umnico contacts with username (matchable): {len(umnico_contacts)}")

    # Now match: for each lead with NICK, find if there's a matching Umnico contact
    duplicates = []

    for lead_id, lead_data in leads_nick.items():
        nick_normalized = normalize_username(lead_data["nick"])
        if not nick_normalized:
            continue

        # Check if this nick matches any Umnico contact
        if nick_normalized in umnico_contacts:
            new_contact = umnico_contacts[nick_normalized]

            # Find the old contact linked to this lead
            for old_contact_id in lead_data["contact_ids"]:
                old_contact = contact_map.get(old_contact_id)
                if not old_contact:
                    continue

                # Skip if same contact
                if old_contact["id"] == new_contact["id"]:
                    continue

                # This is a duplicate!
                old_leads = [l["id"] for l in (old_contact.get("_embedded") or {}).get("leads") or []]
                new_leads = [l["id"] for l in (new_contact.get("_embedded") or {}).get("leads") or []]

                duplicates.append({
                    "username": nick_normalized,
                    "nick_raw": lead_data["nick"],
                    "old_contact_id": old_contact["id"],
                    "old_contact_name": old_contact.get("name", "N/A"),
                    "old_contact_created": old_contact.get("created_at", 0),
                    "old_lead_count": len(old_leads),
                    "old_lead_ids": old_leads,
                    "new_contact_id": new_contact["id"],
                    "new_contact_name": new_contact.get("name", "N/A"),
                    "new_contact_created": new_contact.get("created_at", 0),
                    "new_lead_count": len(new_leads),
                    "new_lead_ids": new_leads,
                    "umnico_social_id": new_contact.get("_umnico_social", ""),
                    "match_lead_id": lead_id,
                })

    # Also find contacts with same name but no NICK match (for manual review)
    name_groups = {}
    for c in contacts:
        name = (c.get("name") or "").strip().lower()
        if name and len(name) > 2:
            name_groups.setdefault(name, []).append(c)

    name_dupes = 0
    for name, group in name_groups.items():
        if len(group) > 1:
            has_umnico = any(c.get("_has_umnico") for c in group)
            has_old = any(not c.get("_has_umnico") for c in group)
            if has_umnico and has_old:
                name_dupes += 1

    print(f"  Username matches: {len(duplicates)}")
    print(f"  Name-only potential dupes (for manual review): {name_dupes}")

    # Show sample of NICK values and Umnico logins for debugging
    if leads_nick:
        print(f"\n  Sample NICK values from leads:")
        for i, (lid, ld) in enumerate(list(leads_nick.items())[:5]):
            print(f"    Lead {lid}: NICK='{ld['nick']}' -> normalized='{normalize_username(ld['nick'])}'")

    if umnico_contacts:
        print(f"\n  Sample Umnico contact logins:")
        for i, (uname, uc) in enumerate(list(umnico_contacts.items())[:5]):
            print(f"    Contact {uc['id']}: login='{uname}', socialId='{uc.get('_umnico_social', '')}'")

    return duplicates


def generate_report(duplicates: list, output_path: str):
    """Generate CSV report of found duplicates."""
    print(f"[5/5] Generating report -> {output_path}")

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "username",
            "nick_raw",
            "old_contact_id",
            "old_contact_name",
            "old_contact_created",
            "old_lead_count",
            "old_lead_ids",
            "new_contact_id",
            "new_contact_name",
            "new_contact_created",
            "new_lead_count",
            "new_lead_ids",
            "umnico_social_id",
            "match_lead_id",
            "recommendation",
        ])
        writer.writeheader()

        for dup in duplicates:
            # Determine recommendation
            if dup["old_lead_count"] >= dup["new_lead_count"]:
                rec = f"MERGE new({dup['new_contact_id']}) -> old({dup['old_contact_id']})"
            else:
                rec = f"MERGE old({dup['old_contact_id']}) -> new({dup['new_contact_id']}) [REVIEW: new has more leads]"

            writer.writerow({
                **dup,
                "old_lead_ids": ";".join(str(x) for x in dup["old_lead_ids"]),
                "new_lead_ids": ";".join(str(x) for x in dup["new_lead_ids"]),
                "recommendation": rec,
            })

    print(f"  Written {len(duplicates)} duplicate pairs to {output_path}")


def print_summary(duplicates: list):
    """Print human-readable summary."""
    print("\n" + "=" * 60)
    print("DUPLICATE REPORT SUMMARY")
    print("=" * 60)
    print(f"Total duplicate pairs found: {len(duplicates)}")
    print()

    if not duplicates:
        print("No duplicates found by username matching.")
        print("Consider checking by name similarity (manual review).")
        return

    total_old_leads = sum(d["old_lead_count"] for d in duplicates)
    total_new_leads = sum(d["new_lead_count"] for d in duplicates)

    print(f"Old contacts affected: {len(set(d['old_contact_id'] for d in duplicates))}")
    print(f"New contacts (from Umnico): {len(set(d['new_contact_id'] for d in duplicates))}")
    print(f"Old leads linked: {total_old_leads}")
    print(f"New leads linked: {total_new_leads}")
    print()

    print("TOP 10 DUPLICATES:")
    print("-" * 60)
    for i, dup in enumerate(duplicates[:10], 1):
        print(f"{i}. @{dup['username']}")
        print(f"   OLD: contact {dup['old_contact_id']} \"{dup['old_contact_name']}\" ({dup['old_lead_count']} leads)")
        print(f"   NEW: contact {dup['new_contact_id']} \"{dup['new_contact_name']}\" ({dup['new_lead_count']} leads)")
        print(f"   Umnico ID: {dup['umnico_social_id']}")
        print()


def main():
    parser = argparse.ArgumentParser(description="AmoCRM Duplicate Scout (Read Only)")
    parser.add_argument("--token", required=True, help="amoCRM API token")
    parser.add_argument("--output", default="dedup_report.csv", help="Output CSV path")
    args = parser.parse_args()

    print(f"AmoCRM Duplicate Scout v0.2")
    print(f"Domain: {AMOCRM_DOMAIN}")
    print(f"Mode: READ ONLY — no changes will be made")
    print(f"Time: {datetime.now().isoformat()}")
    print()

    # Step 1: Detect contact fields
    contact_fields = detect_contact_fields(args.token)
    CONTACT_FIELD_IDS.update(contact_fields)

    # Step 2: Get all contacts
    contacts = get_all_contacts(args.token)
    print(f"  Total contacts: {len(contacts)}")

    # Step 3: Get leads with NICK
    leads_nick = get_all_leads_with_nick(args.token)
    print(f"  Leads with NICK field: {len(leads_nick)}")

    # Step 4: Find duplicates
    duplicates = find_duplicates(contacts, leads_nick, contact_fields)

    # Step 5: Generate report
    generate_report(duplicates, args.output)
    print_summary(duplicates)

    print(f"\nFull report saved to: {args.output}")
    print("Review the report before proceeding to Phase 1 (test merge).")


if __name__ == "__main__":
    main()
