"""
Phase 2: AmoCRM Mass Merge — All Duplicate Pairs
Processes all duplicate pairs from dedup_report.csv.

For each pair:
  1. Backup both contacts (full JSON)
  2. Link new contact's leads to old contact
  3. Copy Umnico fields to old contact
  4. Close duplicate leads as "Double"
  5. Unlink leads from new contact

Handles edge cases:
  - 1 new contact → multiple old contacts: merges into oldest/most-leads old contact
  - Duplicate rows: deduplicates by (old_id, new_id) pair
  - Already-closed leads: skips closing

Usage:
    # Dry run (shows plan, no changes):
    python phase2_mass_merge.py --token TOKEN

    # Execute all merges:
    python phase2_mass_merge.py --token TOKEN --execute

    # Execute with limit (e.g., first 5 pairs):
    python phase2_mass_merge.py --token TOKEN --execute --limit 5
"""

import argparse
import csv
import json
import time
import sys
import os
import io
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from datetime import datetime

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

AMOCRM_DOMAIN = "migratoramocrm.amocrm.ru"
BASE_URL = f"https://{AMOCRM_DOMAIN}/api/v4"
BACKUP_DIR = "backups"
REPORT_FILE = "dedup_report.csv"

# Status & field IDs
CLOSED_STATUS_ID = 143
LOSS_REASON_FIELD_ID = 1631379
LOSS_REASON_DOUBLE_ENUM = 4661359

# Already merged pairs (from Phase 1 testing)
ALREADY_MERGED = {
    (33296981, 40028311),  # @sergey07051979
}


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
            print("    [!] Rate limited, waiting 3s...")
            time.sleep(3)
            return api_get(path, token, params)
        body = e.read().decode()[:300]
        print(f"    [!] API Error {e.code}: {body}")
        return None


def api_patch(path: str, token: str, data) -> dict | None:
    url = f"{BASE_URL}{path}"
    payload = json.dumps(data).encode("utf-8")
    req = Request(url, data=payload, method="PATCH", headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    try:
        with urlopen(req) as resp:
            body = resp.read().decode()
            time.sleep(0.15)
            if not body.strip():
                return {}
            return json.loads(body)
    except HTTPError as e:
        body = e.read().decode()[:300]
        print(f"    [!] API Error {e.code}: {body}")
        return None


def api_post(path: str, token: str, data) -> dict | None:
    url = f"{BASE_URL}{path}"
    payload = json.dumps(data).encode("utf-8")
    req = Request(url, data=payload, method="POST", headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    try:
        with urlopen(req) as resp:
            body = resp.read().decode()
            time.sleep(0.15)
            if not body.strip():
                return {}
            return json.loads(body)
    except HTTPError as e:
        body = e.read().decode()[:300]
        print(f"    [!] API Error {e.code}: {body}")
        return None


def load_report() -> list:
    """Load and deduplicate pairs from CSV report."""
    with open(REPORT_FILE, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    # Group by new_contact_id to handle 1-to-many
    from collections import defaultdict
    by_new = defaultdict(list)
    for r in rows:
        old_id = int(r["old_contact_id"])
        new_id = int(r["new_contact_id"])
        by_new[new_id].append(r)

    # Build unique merge tasks
    tasks = []
    seen_pairs = set()

    for new_id, matches in by_new.items():
        # Pick primary old contact: most leads, then oldest
        best = max(matches, key=lambda r: (int(r["old_lead_count"]), -int(r["old_contact_created"])))
        old_id = int(best["old_contact_id"])

        pair = (old_id, new_id)
        if pair in seen_pairs:
            continue
        if pair in ALREADY_MERGED:
            continue
        seen_pairs.add(pair)

        tasks.append({
            "old_contact_id": old_id,
            "new_contact_id": new_id,
            "username": best["username"],
            "old_name": best["old_contact_name"],
            "new_name": best["new_contact_name"],
            "old_lead_count": int(best["old_lead_count"]),
            "new_lead_count": int(best["new_lead_count"]),
        })

    return tasks


def backup_pair(old_id: int, new_id: int, token: str, timestamp: str) -> str:
    """Backup both contacts + leads to JSON."""
    os.makedirs(BACKUP_DIR, exist_ok=True)

    old_contact = api_get(f"/contacts/{old_id}", token, {"with": "leads"})
    new_contact = api_get(f"/contacts/{new_id}", token, {"with": "leads"})

    # Fetch leads details
    old_leads = []
    if old_contact:
        for lr in (old_contact.get("_embedded") or {}).get("leads") or []:
            lead = api_get(f"/leads/{lr['id']}", token)
            if lead:
                old_leads.append(lead)

    new_leads = []
    if new_contact:
        for lr in (new_contact.get("_embedded") or {}).get("leads") or []:
            lead = api_get(f"/leads/{lr['id']}", token)
            if lead:
                new_leads.append(lead)

    backup = {
        "backup_created": datetime.now().isoformat(),
        "old_contact": {"contact": old_contact, "leads": old_leads},
        "new_contact": {"contact": new_contact, "leads": new_leads},
    }

    path = os.path.join(BACKUP_DIR, f"merge_{old_id}_{new_id}_{timestamp}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(backup, f, ensure_ascii=False, indent=2)

    return path


def merge_pair(old_id: int, new_id: int, token: str) -> dict:
    """Execute manual merge for one pair. Returns status dict."""
    result = {"old_id": old_id, "new_id": new_id, "steps": []}

    # Fetch both contacts
    old_contact = api_get(f"/contacts/{old_id}", token, {"with": "leads"})
    new_contact = api_get(f"/contacts/{new_id}", token, {"with": "leads"})

    if not old_contact or not new_contact:
        result["status"] = "FAILED"
        result["error"] = "Cannot fetch contacts"
        return result

    # Get new contact's leads
    new_lead_refs = (new_contact.get("_embedded") or {}).get("leads") or []
    new_lead_ids = [lr["id"] for lr in new_lead_refs]

    # Get old contact's existing field IDs
    old_field_ids = {cf["field_id"] for cf in old_contact.get("custom_fields_values") or []}

    # Step 1: Link new leads to old contact
    if new_lead_ids:
        link_data = [{"to_entity_id": lid, "to_entity_type": "leads"} for lid in new_lead_ids]
        link_result = api_post(f"/contacts/{old_id}/link", token, link_data)
        if link_result is None:
            result["status"] = "PARTIAL"
            result["steps"].append("link: FAILED")
        else:
            result["steps"].append(f"link: {len(new_lead_ids)} leads")

    # Step 2: Copy custom fields
    new_fields = new_contact.get("custom_fields_values") or []
    fields_to_copy = []
    for cf in new_fields:
        if cf.get("values") and cf["field_id"] not in old_field_ids:
            fields_to_copy.append({"field_id": cf["field_id"], "values": cf["values"]})

    if fields_to_copy:
        update_data = [{"id": old_id, "custom_fields_values": fields_to_copy}]
        patch_result = api_patch("/contacts", token, update_data)
        if patch_result is None:
            result["steps"].append(f"fields: FAILED ({len(fields_to_copy)} fields)")
        else:
            result["steps"].append(f"fields: copied {len(fields_to_copy)}")

    # Step 3: Close duplicate leads as Double
    closed_count = 0
    for lid in new_lead_ids:
        lead = api_get(f"/leads/{lid}", token)
        if not lead:
            continue
        if lead.get("status_id") == CLOSED_STATUS_ID:
            closed_count += 1
            continue

        close_data = [{
            "id": lid,
            "status_id": CLOSED_STATUS_ID,
            "custom_fields_values": [{
                "field_id": LOSS_REASON_FIELD_ID,
                "values": [{"enum_id": LOSS_REASON_DOUBLE_ENUM}]
            }]
        }]
        close_result = api_patch("/leads", token, close_data)
        if close_result is not None:
            closed_count += 1

    if new_lead_ids:
        result["steps"].append(f"close: {closed_count}/{len(new_lead_ids)} leads")

    # Step 4: Unlink leads from new contact
    if new_lead_ids:
        unlink_data = [{"to_entity_id": lid, "to_entity_type": "leads"} for lid in new_lead_ids]
        unlink_result = api_post(f"/contacts/{new_id}/unlink", token, unlink_data)
        if unlink_result is None:
            result["steps"].append("unlink: FAILED")
        else:
            result["steps"].append("unlink: OK")

    result["status"] = "OK"
    return result


def main():
    parser = argparse.ArgumentParser(description="AmoCRM Mass Merge (Phase 2)")
    parser.add_argument("--token", required=True, help="amoCRM API token")
    parser.add_argument("--execute", action="store_true", help="Actually execute merges")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of pairs to process")
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"AmoCRM Mass Merge — Phase 2")
    print(f"Time: {datetime.now().isoformat()}")
    print(f"Mode: {'EXECUTE' if args.execute else 'DRY RUN'}")
    if args.limit:
        print(f"Limit: {args.limit} pairs")
    print()

    # Load tasks
    tasks = load_report()
    print(f"Loaded {len(tasks)} unique merge tasks (excluding already merged)")

    if args.limit:
        tasks = tasks[:args.limit]
        print(f"Processing first {len(tasks)} tasks")

    # Show plan
    print(f"\n{'='*70}")
    print(f"MERGE PLAN")
    print(f"{'='*70}")
    for i, t in enumerate(tasks, 1):
        print(f"  {i:3d}. @{t['username']:25s}  old={t['old_contact_id']} \"{t['old_name']}\" ({t['old_lead_count']}L)"
              f"  <-  new={t['new_contact_id']} \"{t['new_name']}\" ({t['new_lead_count']}L)")
    print(f"{'='*70}")

    if not args.execute:
        print(f"\nDRY RUN — no changes made.")
        print(f"To execute: add --execute flag")
        print(f"To test first N: add --limit N")
        return

    # Execute
    print(f"\nStarting mass merge of {len(tasks)} pairs...\n")

    results = {"ok": 0, "failed": 0, "partial": 0}
    log_path = os.path.join(BACKUP_DIR, f"mass_merge_log_{timestamp}.json")
    log_entries = []

    for i, t in enumerate(tasks, 1):
        old_id = t["old_contact_id"]
        new_id = t["new_contact_id"]
        username = t["username"]

        print(f"[{i}/{len(tasks)}] @{username} — old={old_id} <- new={new_id}")

        # Backup
        try:
            backup_path = backup_pair(old_id, new_id, args.token, timestamp)
            print(f"  Backup: {backup_path}")
        except Exception as e:
            print(f"  [!] Backup failed: {e}")
            print(f"  SKIPPING this pair for safety")
            results["failed"] += 1
            log_entries.append({"pair": t, "status": "SKIP_BACKUP_FAILED", "error": str(e)})
            continue

        # Merge
        try:
            merge_result = merge_pair(old_id, new_id, args.token)
            status = merge_result["status"]
            steps = ", ".join(merge_result["steps"])
            print(f"  Result: {status} ({steps})")

            results[status.lower()] = results.get(status.lower(), 0) + 1
            log_entries.append({"pair": t, **merge_result})
        except Exception as e:
            print(f"  [!] Merge error: {e}")
            results["failed"] += 1
            log_entries.append({"pair": t, "status": "ERROR", "error": str(e)})

        print()

    # Save log
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": timestamp,
            "total": len(tasks),
            "results": results,
            "entries": log_entries,
        }, f, ensure_ascii=False, indent=2)

    # Summary
    print(f"\n{'='*70}")
    print(f"MASS MERGE COMPLETE")
    print(f"{'='*70}")
    print(f"  Total processed: {len(tasks)}")
    print(f"  OK:      {results['ok']}")
    print(f"  Failed:  {results['failed']}")
    print(f"  Partial: {results['partial']}")
    print(f"\n  Full log: {log_path}")
    print(f"  Backups:  {BACKUP_DIR}/")


if __name__ == "__main__":
    main()
