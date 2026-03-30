"""
Phase 0b: AmoCRM Name-Only Duplicates — READ ONLY
Finds contacts that share the same name where one is from Umnico and one is old.
These were NOT matched by Telegram username and need manual review.

Usage:
    python phase0_name_dupes.py --token YOUR_TOKEN
    python phase0_name_dupes.py --token YOUR_TOKEN --output name_dupes_review.csv
"""

import argparse
import csv
import json
import time
import sys
import io
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from datetime import datetime

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

AMOCRM_DOMAIN = "migratoramocrm.amocrm.ru"
BASE_URL = f"https://{AMOCRM_DOMAIN}/api/v4"

KNOWN_CONTACT_FIELDS = {
    130527: "telegram_id",
    1648299: "telegram_username",
    1648301: "telegram_id_wz",
    1654991: "umnico_social_id",
    1654993: "umnico_customer_id",
    1655001: "login",
}


def _has_next_page(data: dict) -> bool:
    return "next" in data.get("_links", {})


def api_get(path: str, token: str, params: dict = None) -> dict | list | None:
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
            body = resp.read().decode()
            time.sleep(0.15)
            if not body.strip():
                return None
            return json.loads(body)
    except HTTPError as e:
        if e.code == 204:
            return None
        if e.code == 429:
            print("  [!] Rate limited, waiting 3s...")
            time.sleep(3)
            return api_get(path, token, params)
        print(f"  [!] API Error {e.code}: {e.read().decode()[:200]}")
        return None


def get_all_contacts(token: str) -> list:
    print("[1/3] Fetching all contacts...")
    contacts = []
    page = 1
    while True:
        data = api_get("/contacts", token, {"page": page, "limit": 250, "with": "leads"})
        if not data or "_embedded" not in data:
            break
        batch = data["_embedded"]["contacts"]
        contacts.extend(batch)
        print(f"  Page {page}: {len(batch)} contacts (total: {len(contacts)})")
        if not _has_next_page(data):
            break
        page += 1
    return contacts


def find_name_dupes(contacts: list) -> list:
    print("[2/3] Analyzing name-only duplicates...")

    # Tag each contact: has_umnico or not
    for c in contacts:
        has_umnico = False
        login_val = None
        for cf in c.get("custom_fields_values") or []:
            if cf["field_id"] in (1654991, 1654993):  # umnico_social_id or umnico_customer_id
                vals = cf.get("values", [])
                if vals and str(vals[0].get("value", "")).strip():
                    has_umnico = True
            if cf["field_id"] == 1655001:  # login
                vals = cf.get("values", [])
                if vals:
                    login_val = str(vals[0].get("value", "")).strip()
        c["_has_umnico"] = has_umnico
        c["_login"] = login_val

    # Group by normalized name
    name_groups = {}
    for c in contacts:
        name = (c.get("name") or "").strip().lower()
        if name and len(name) > 2:
            name_groups.setdefault(name, []).append(c)

    # Find groups with both Umnico and non-Umnico contacts
    dupes = []
    for name, group in sorted(name_groups.items()):
        if len(group) < 2:
            continue

        umnico_contacts = [c for c in group if c["_has_umnico"]]
        old_contacts = [c for c in group if not c["_has_umnico"]]

        if not umnico_contacts or not old_contacts:
            continue

        # Each (old, new) pair is a potential duplicate
        for old_c in old_contacts:
            old_leads = [l["id"] for l in (old_c.get("_embedded") or {}).get("leads") or []]
            for new_c in umnico_contacts:
                new_leads = [l["id"] for l in (new_c.get("_embedded") or {}).get("leads") or []]
                dupes.append({
                    "name": (old_c.get("name") or "").strip(),
                    "old_contact_id": old_c["id"],
                    "old_contact_name": old_c.get("name", ""),
                    "old_lead_count": len(old_leads),
                    "old_lead_ids": ";".join(str(x) for x in old_leads),
                    "new_contact_id": new_c["id"],
                    "new_contact_name": new_c.get("name", ""),
                    "new_contact_login": new_c.get("_login", ""),
                    "new_lead_count": len(new_leads),
                    "new_lead_ids": ";".join(str(x) for x in new_leads),
                    "recommendation": "MANUAL REVIEW — matched by name only",
                })

    print(f"  Name groups with mixed old+Umnico: {len([1 for n, g in name_groups.items() if len(g) >= 2 and any(c['_has_umnico'] for c in g) and any(not c['_has_umnico'] for c in g)])}")
    print(f"  Total (old, new) pairs for review: {len(dupes)}")
    return dupes


def generate_report(dupes: list, output_path: str):
    print(f"[3/3] Generating report -> {output_path}")
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "name",
            "old_contact_id", "old_contact_name", "old_lead_count", "old_lead_ids",
            "new_contact_id", "new_contact_name", "new_contact_login",
            "new_lead_count", "new_lead_ids",
            "recommendation",
        ])
        writer.writeheader()
        for d in dupes:
            writer.writerow(d)
    print(f"  Written {len(dupes)} pairs to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="AmoCRM Name-Only Duplicates (Read Only)")
    parser.add_argument("--token", required=True, help="amoCRM API token")
    parser.add_argument("--output", default="name_dupes_review.csv", help="Output CSV path")
    args = parser.parse_args()

    print(f"AmoCRM Name-Only Duplicate Finder")
    print(f"Domain: {AMOCRM_DOMAIN}")
    print(f"Mode: READ ONLY")
    print(f"Time: {datetime.now().isoformat()}")
    print()

    contacts = get_all_contacts(args.token)
    print(f"  Total contacts: {len(contacts)}")

    dupes = find_name_dupes(contacts)
    generate_report(dupes, args.output)

    print(f"\nReport saved to: {args.output}")
    print("Review each pair manually before merging.")


if __name__ == "__main__":
    main()
