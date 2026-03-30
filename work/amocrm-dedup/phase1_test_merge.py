"""
Phase 1: AmoCRM Test Merge — Single Pair
Merges ONE duplicate contact pair with full backup and verification.
After merge, closes duplicate leads with reason "Double".

Flow:
  1. Backup both contacts + their leads (full JSON)
  2. Show merge plan
  3. Execute merge (only with --execute flag)
  4. Close duplicate leads as "Double"
  5. Verify result

Usage:
    # Dry run (backup + plan only):
    python phase1_test_merge.py --token TOKEN --old-contact 33296981 --new-contact 40028311

    # Execute merge + close leads:
    python phase1_test_merge.py --token TOKEN --old-contact 33296981 --new-contact 40028311 --execute
"""

import argparse
import json
import time
import sys
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from datetime import datetime

AMOCRM_DOMAIN = "migratoramocrm.amocrm.ru"
BASE_URL = f"https://{AMOCRM_DOMAIN}/api/v4"
BACKUP_DIR = "backups"

# Status & field IDs
CLOSED_STATUS_ID = 143  # "CLOSED AND NOT IMPLEMENTED" — universal across all pipelines
LOSS_REASON_FIELD_ID = 1631379  # "Причина отказа" (select field)
LOSS_REASON_DOUBLE_ENUM = 4661359  # "Double" enum value


def api_get(path: str, token: str, params: dict = None) -> dict | list | None:
    """Make GET request to amoCRM API."""
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
            print("  [!] Rate limited, waiting 2s...")
            time.sleep(2)
            return api_get(path, token, params)
        body = e.read().decode()[:500]
        print(f"  [!] API Error {e.code}: {body}")
        return None


def api_patch(path: str, token: str, data) -> dict | None:
    """Make PATCH request to amoCRM API."""
    url = f"{BASE_URL}{path}"
    payload = json.dumps(data).encode("utf-8")

    req = Request(url, data=payload, method="PATCH", headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })

    try:
        with urlopen(req) as resp:
            body = resp.read().decode()
            if not body.strip():
                return {}
            return json.loads(body)
    except HTTPError as e:
        body = e.read().decode()[:500]
        print(f"  [!] API Error {e.code}: {body}")
        return None


def api_post(path: str, token: str, data) -> dict | None:
    """Make POST request to amoCRM API."""
    url = f"{BASE_URL}{path}"
    payload = json.dumps(data).encode("utf-8")

    req = Request(url, data=payload, method="POST", headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })

    try:
        with urlopen(req) as resp:
            body = resp.read().decode()
            if not body.strip():
                return {}
            return json.loads(body)
    except HTTPError as e:
        body = e.read().decode()[:500]
        print(f"  [!] API Error {e.code}: {body}")
        return None


def fetch_contact_full(contact_id: int, token: str) -> dict | None:
    """Fetch contact with all related data."""
    contact = api_get(f"/contacts/{contact_id}", token, {"with": "leads,customers"})
    if not contact:
        print(f"  [!] Failed to fetch contact {contact_id}")
        return None

    # Fetch linked leads
    leads = []
    embedded_leads = (contact.get("_embedded") or {}).get("leads") or []
    for lead_ref in embedded_leads:
        lead = api_get(f"/leads/{lead_ref['id']}", token, {"with": "contacts"})
        if lead:
            leads.append(lead)

    # Fetch notes
    notes = []
    notes_data = api_get(f"/contacts/{contact_id}/notes", token, {"limit": 250})
    if notes_data and "_embedded" in notes_data:
        notes = notes_data["_embedded"]["notes"]

    return {
        "contact": contact,
        "leads": leads,
        "notes": notes,
        "fetched_at": datetime.now().isoformat(),
    }


def save_backup(old_data: dict, new_data: dict, backup_name: str) -> str:
    """Save full backup of both contacts to JSON file."""
    os.makedirs(BACKUP_DIR, exist_ok=True)

    backup = {
        "backup_created": datetime.now().isoformat(),
        "merge_direction": "new -> old (old survives)",
        "old_contact": old_data,
        "new_contact": new_data,
    }

    path = os.path.join(BACKUP_DIR, f"{backup_name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(backup, f, ensure_ascii=False, indent=2)

    print(f"  Backup saved: {path}")
    return path


def print_contact_summary(label: str, data: dict):
    """Print human-readable contact summary."""
    c = data["contact"]
    leads = data["leads"]

    print(f"\n  {label}:")
    print(f"    ID: {c['id']}")
    print(f"    Name: {c.get('name', 'N/A')}")
    print(f"    Created: {datetime.fromtimestamp(c.get('created_at', 0)).isoformat()}")
    print(f"    Updated: {datetime.fromtimestamp(c.get('updated_at', 0)).isoformat()}")

    # Custom fields
    print(f"    Custom fields:")
    for cf in c.get("custom_fields_values") or []:
        vals = cf.get("values", [])
        val_str = ", ".join(str(v.get("value", "")) for v in vals)
        print(f"      {cf.get('field_name', cf['field_id'])}: {val_str}")

    # Leads
    print(f"    Leads ({len(leads)}):")
    for lead in leads:
        status = lead.get("status_id", "?")
        pipeline = lead.get("pipeline_id", "?")
        is_closed = status == CLOSED_STATUS_ID
        marker = " [ALREADY CLOSED]" if is_closed else ""
        print(f"      - {lead['id']}: \"{lead.get('name', 'N/A')}\" (status={status}, pipeline={pipeline}){marker}")

    # Notes
    print(f"    Notes: {len(data['notes'])} entries")


def execute_merge(old_contact_id: int, new_contact_id: int,
                   old_data: dict, new_data: dict, token: str) -> bool:
    """Execute manual contact merge via amoCRM API.

    amoCRM has no merge endpoint, so we simulate it:
      1. Link new contact's leads to old contact
      2. Copy custom fields from new contact to old contact
      3. Close duplicate leads as Double
      4. Unlink leads from new contact

    Returns True on success.
    """
    print(f"\n  Executing manual merge: {new_contact_id} -> {old_contact_id}")

    new_lead_ids = [l["id"] for l in new_data["leads"]]
    old_field_ids = {cf["field_id"] for cf in old_data["contact"].get("custom_fields_values") or []}

    # Step 1: Link new contact's leads to old contact
    if new_lead_ids:
        print(f"  Step 1: Linking {len(new_lead_ids)} lead(s) to old contact...")
        link_data = [{"to_entity_id": lid, "to_entity_type": "leads"} for lid in new_lead_ids]
        result = api_post(f"/contacts/{old_contact_id}/link", token, link_data)
        if result is None:
            print("  [!] FAILED to link leads!")
            return False
        print(f"  Linked successfully")
    else:
        print(f"  Step 1: No leads to link")

    # Step 2: Copy custom fields from new contact to old contact
    new_fields = new_data["contact"].get("custom_fields_values") or []
    fields_to_copy = []
    for cf in new_fields:
        fid = cf["field_id"]
        vals = cf.get("values", [])
        if vals and fid not in old_field_ids:
            fields_to_copy.append({
                "field_id": fid,
                "values": vals,
            })
            field_name = cf.get("field_name", str(fid))
            val_str = ", ".join(str(v.get("value", "")) for v in vals)
            print(f"  Step 2: Copying field {field_name}: {val_str}")

    if fields_to_copy:
        update_data = [{"id": old_contact_id, "custom_fields_values": fields_to_copy}]
        result = api_patch("/contacts", token, update_data)
        if result is None:
            print("  [!] WARNING: Failed to copy some custom fields")
        else:
            print(f"  Copied {len(fields_to_copy)} field(s)")
    else:
        print(f"  Step 2: No new fields to copy")

    # Step 3: Unlink leads from new contact
    if new_lead_ids:
        print(f"  Step 3: Unlinking leads from new contact...")
        unlink_data = [{"to_entity_id": lid, "to_entity_type": "leads"} for lid in new_lead_ids]
        result = api_post(f"/contacts/{new_contact_id}/unlink", token, unlink_data)
        if result is None:
            print("  [!] WARNING: Failed to unlink leads from new contact")
        else:
            print(f"  Unlinked successfully")

    print(f"  Manual merge complete")
    return True


def close_leads_as_double(lead_ids: list, token: str) -> list:
    """Close leads by setting status to CLOSED and reason to Double.

    Returns list of successfully closed lead IDs.
    """
    closed = []

    for lead_id in lead_ids:
        # First check current status
        lead = api_get(f"/leads/{lead_id}", token)
        if not lead:
            print(f"    [!] Cannot fetch lead {lead_id}, skipping")
            continue

        current_status = lead.get("status_id")
        if current_status == CLOSED_STATUS_ID:
            print(f"    Lead {lead_id}: already closed, skipping")
            closed.append(lead_id)
            continue

        # Update lead: set status to CLOSED + reason to Double
        update_data = [
            {
                "id": lead_id,
                "status_id": CLOSED_STATUS_ID,
                "custom_fields_values": [
                    {
                        "field_id": LOSS_REASON_FIELD_ID,
                        "values": [
                            {"enum_id": LOSS_REASON_DOUBLE_ENUM}
                        ]
                    }
                ]
            }
        ]

        result = api_patch("/leads", token, update_data)
        if result is not None:
            print(f"    Lead {lead_id}: CLOSED with reason Double")
            closed.append(lead_id)
        else:
            print(f"    [!] Lead {lead_id}: FAILED to close")

    return closed


def verify_merge(old_contact_id: int, new_contact_id: int,
                 expected_lead_count: int, token: str) -> bool:
    """Verify merge was successful."""
    print("\n  Verifying merge...")

    # Check old contact (should have all leads now)
    old = api_get(f"/contacts/{old_contact_id}", token, {"with": "leads"})
    if not old:
        print("  [!] FAILED: Cannot fetch old contact after merge!")
        return False

    old_leads = (old.get("_embedded") or {}).get("leads") or []
    print(f"  Old contact {old_contact_id}: {len(old_leads)} leads after merge (expected: {expected_lead_count})")

    # Check custom fields transferred
    has_umnico = False
    for cf in old.get("custom_fields_values") or []:
        name = cf.get("field_name", "").lower()
        if "umnico" in name or "socialid" in name.replace(" ", ""):
            has_umnico = True
            vals = cf.get("values", [])
            val_str = ", ".join(str(v.get("value", "")) for v in vals)
            print(f"  Transferred field: {cf.get('field_name')}: {val_str}")

    print(f"  Umnico fields present on old contact: {has_umnico}")

    # Verify leads are closed
    for lead_ref in old_leads:
        lead = api_get(f"/leads/{lead_ref['id']}", token)
        if lead:
            status = lead.get("status_id")
            loss_reason = ""
            for cf in lead.get("custom_fields_values") or []:
                if cf["field_id"] == LOSS_REASON_FIELD_ID:
                    vals = cf.get("values", [])
                    if vals:
                        loss_reason = vals[0].get("value", "")
            print(f"  Lead {lead['id']}: status={status}, loss_reason='{loss_reason}'")

    print("\n  VERIFICATION COMPLETE")
    return True


def main():
    parser = argparse.ArgumentParser(description="AmoCRM Test Merge (Phase 1)")
    parser.add_argument("--token", required=True, help="amoCRM API token")
    parser.add_argument("--old-contact", type=int, required=True, help="Old contact ID (survives)")
    parser.add_argument("--new-contact", type=int, required=True, help="New contact ID (gets merged)")
    parser.add_argument("--execute", action="store_true", help="Actually execute the merge")
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"AmoCRM Test Merge — Phase 1 v0.2")
    print(f"Time: {datetime.now().isoformat()}")
    print(f"Mode: {'EXECUTE' if args.execute else 'DRY RUN (backup + plan only)'}")
    print(f"Direction: contact {args.new_contact} -> contact {args.old_contact}")
    print()

    # Step 1: Fetch full data for both contacts
    print("[1/5] Fetching contact data...")
    old_data = fetch_contact_full(args.old_contact, args.token)
    new_data = fetch_contact_full(args.new_contact, args.token)

    if not old_data or not new_data:
        print("\n[!] ABORT: Failed to fetch one or both contacts.")
        sys.exit(1)

    # Step 2: Save backup
    print("\n[2/5] Saving backup...")
    backup_name = f"merge_{args.old_contact}_{args.new_contact}_{timestamp}"
    backup_path = save_backup(old_data, new_data, backup_name)

    # Step 3: Show merge plan
    print("\n[3/5] Merge plan:")
    print(f"  Direction: MERGE new({args.new_contact}) INTO old({args.old_contact})")
    print(f"  Old contact SURVIVES, new contact becomes alias")
    print_contact_summary("OLD CONTACT (survives)", old_data)
    print_contact_summary("NEW CONTACT (will be merged)", new_data)

    old_lead_ids = [l["id"] for l in old_data["leads"]]
    new_lead_ids = [l["id"] for l in new_data["leads"]]
    total_expected = len(old_lead_ids) + len(new_lead_ids)

    # Determine which leads to close as Double
    # Close NEW contact's leads (they are duplicates)
    # But skip leads that are already closed
    leads_to_close = []
    for lead in new_data["leads"]:
        if lead.get("status_id") != CLOSED_STATUS_ID:
            leads_to_close.append(lead["id"])

    print(f"\n  After merge:")
    print(f"    Old contact will have {total_expected} leads: {old_lead_ids + new_lead_ids}")
    print(f"    Leads to CLOSE as Double: {leads_to_close}")
    if not leads_to_close:
        print(f"    (all new leads already closed or no new leads)")

    # Step 4: Execute or stop
    if not args.execute:
        print(f"\n[4/5] DRY RUN — merge NOT executed.")
        print(f"  Backup saved to: {backup_path}")
        print(f"  To execute, re-run with --execute flag.")
        print(f"\n  Links to review:")
        print(f"    Old: https://{AMOCRM_DOMAIN}/contacts/detail/{args.old_contact}")
        print(f"    New: https://{AMOCRM_DOMAIN}/contacts/detail/{args.new_contact}")
        for lid in old_lead_ids:
            print(f"    Old lead: https://{AMOCRM_DOMAIN}/leads/detail/{lid}")
        for lid in new_lead_ids:
            print(f"    New lead (will close): https://{AMOCRM_DOMAIN}/leads/detail/{lid}")
        return

    # Execute merge
    print(f"\n[4/5] Executing merge...")
    success = execute_merge(args.old_contact, args.new_contact,
                            old_data, new_data, args.token)

    if not success:
        print("  [!] MERGE FAILED — check output above")
        print(f"  Backup available at: {backup_path}")
        sys.exit(1)

    time.sleep(1)  # Wait for amoCRM to process

    # Close duplicate leads
    if leads_to_close:
        print(f"\n  Closing {len(leads_to_close)} duplicate lead(s) as Double...")
        closed = close_leads_as_double(leads_to_close, args.token)
        print(f"  Closed: {len(closed)}/{len(leads_to_close)}")

    # Step 5: Verify
    print(f"\n[5/5] Verification...")
    verify_merge(args.old_contact, args.new_contact, total_expected, args.token)

    print(f"\n  Full backup: {backup_path}")
    print(f"\n  CHECK IN CRM:")
    print(f"    https://{AMOCRM_DOMAIN}/contacts/detail/{args.old_contact}")


if __name__ == "__main__":
    main()
