"""
Copy NICK field from leads to TelegramUsername_WZ field on linked contacts.
Fast version: no per-contact checks, batch PATCH updates.

Usage:
    python nick_to_telegram.py --token-file .token_tmp
    python nick_to_telegram.py --token-file .token_tmp --execute
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

# Field IDs (verified via API 2026-03-17)
LEAD_NICK_FIELD_ID = 1612133        # NICK on leads (@username)
CONTACT_TG_USERNAME_ID = 1648299    # TelegramUsername_WZ on contacts


def api_get(path: str, token: str, params: dict = None):
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
        if e.code == 401:
            print("  [!] Token expired (401). Need to refresh.")
            sys.exit(1)
        try:
            err_body = e.read().decode()[:300]
        except Exception:
            err_body = str(e)
        print(f"  [!] API Error {e.code}: {err_body}")
        return None


def api_patch(path: str, token: str, data):
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
        if e.code == 429:
            print("    [!] Rate limited, waiting 2s...")
            time.sleep(2)
            return api_patch(path, token, data)
        try:
            err_body = e.read().decode()[:300]
        except Exception:
            err_body = str(e)
        print(f"    [!] API Error {e.code}: {err_body}")
        return None


def normalize_nick(raw: str) -> str:
    """Ensure nick has @ prefix."""
    raw = raw.strip()
    if not raw:
        return ""
    if not raw.startswith("@"):
        raw = "@" + raw
    return raw


def scan_leads(token: str) -> dict:
    """Fetch all leads with NICK, return {contact_id: nick_normalized}.

    Deduplicates by contact_id (first NICK wins).
    """
    print("[1/2] Scanning all leads for NICK field...")
    contact_nick = {}  # contact_id -> {nick, lead_id, lead_name}
    page = 1
    total_leads = 0
    t0 = time.time()

    while True:
        data = api_get("/leads", token, {"page": str(page), "limit": "250", "with": "contacts"})
        if not data or "_embedded" not in data:
            break

        batch = data["_embedded"]["leads"]
        total_leads += len(batch)

        for lead in batch:
            # Extract NICK
            nick = None
            for cf in lead.get("custom_fields_values") or []:
                if cf["field_id"] == LEAD_NICK_FIELD_ID:
                    vals = cf.get("values", [])
                    if vals:
                        nick = str(vals[0].get("value", "")).strip()
                    break

            if not nick:
                continue

            contacts = (lead.get("_embedded") or {}).get("contacts") or []
            if not contacts:
                continue

            cid = contacts[0]["id"]
            if cid not in contact_nick:
                contact_nick[cid] = {
                    "nick": normalize_nick(nick),
                    "nick_raw": nick,
                    "lead_id": lead["id"],
                    "lead_name": lead.get("name", ""),
                }

        elapsed = time.time() - t0
        print(f"  Page {page}: +{len(batch)} leads | total: {total_leads} | NICK->contact pairs: {len(contact_nick)} | {elapsed:.1f}s")

        if "next" not in data.get("_links", {}):
            break
        page += 1

    elapsed = time.time() - t0
    print(f"  Done: {total_leads} leads, {len(contact_nick)} unique contacts with NICK ({elapsed:.1f}s)")
    return contact_nick


def batch_update(contact_nick: dict, token: str) -> dict:
    """Update contacts in batches of 50 via PATCH /contacts."""
    items = list(contact_nick.items())
    total = len(items)
    batch_size = 50

    print(f"\n[2/2] Updating {total} contacts (batches of {batch_size})...")
    stats = {"ok": 0, "failed": 0}
    t0 = time.time()

    for i in range(0, total, batch_size):
        batch = items[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size

        patch_data = []
        for cid, info in batch:
            patch_data.append({
                "id": cid,
                "custom_fields_values": [{
                    "field_id": CONTACT_TG_USERNAME_ID,
                    "values": [{"value": info["nick"]}]
                }]
            })

        result = api_patch("/contacts", token, patch_data)

        if result is not None:
            stats["ok"] += len(batch)
            elapsed = time.time() - t0
            print(f"  Batch {batch_num}/{total_batches}: {len(batch)} OK | total: {stats['ok']}/{total} | {elapsed:.1f}s")
        else:
            # Batch failed — retry one by one
            print(f"  Batch {batch_num}/{total_batches}: FAILED, retrying individually...")
            for cid, info in batch:
                r = api_patch("/contacts", token, [{
                    "id": cid,
                    "custom_fields_values": [{
                        "field_id": CONTACT_TG_USERNAME_ID,
                        "values": [{"value": info["nick"]}]
                    }]
                }])
                if r is not None:
                    stats["ok"] += 1
                else:
                    stats["failed"] += 1
                    print(f"    Contact {cid}: FAILED")

    elapsed = time.time() - t0
    print(f"  Done: {stats['ok']} updated, {stats['failed']} failed ({elapsed:.1f}s)")
    return stats


def save_report(contact_nick: dict, output_path: str):
    """Save CSV of all contact-NICK pairs."""
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["contact_id", "nick_normalized", "nick_raw", "lead_id", "lead_name"])
        for cid, info in contact_nick.items():
            writer.writerow([cid, info["nick"], info["nick_raw"], info["lead_id"], info["lead_name"]])
    print(f"  Report: {output_path} ({len(contact_nick)} rows)")


def main():
    parser = argparse.ArgumentParser(description="Copy NICK from leads to TelegramUsername_WZ on contacts")
    parser.add_argument("--token", help="amoCRM API access token")
    parser.add_argument("--token-file", help="File containing the token")
    parser.add_argument("--execute", action="store_true", help="Actually update contacts (default: dry run)")
    parser.add_argument("--output", default="nick_to_telegram_report.csv")
    args = parser.parse_args()

    if args.token_file:
        with open(args.token_file) as f:
            token = f.read().strip()
    elif args.token:
        token = args.token
    else:
        print("ERROR: provide --token or --token-file")
        sys.exit(1)

    print(f"=== NICK -> TelegramUsername_WZ Sync ===")
    print(f"Mode: {'EXECUTE' if args.execute else 'DRY RUN'}")
    print(f"Time: {datetime.now().isoformat()}")
    print()

    # Step 1: Scan leads
    contact_nick = scan_leads(token)
    if not contact_nick:
        print("\nNo leads with NICK found. Nothing to do.")
        return

    # Save report
    save_report(contact_nick, args.output)

    # Step 2: Execute or stop
    if not args.execute:
        print(f"\nDRY RUN complete. {len(contact_nick)} contacts would be updated.")
        print(f"To execute: add --execute")
        return

    stats = batch_update(contact_nick, token)

    print(f"\n{'='*50}")
    print(f"COMPLETE: {stats['ok']} updated, {stats['failed']} failed")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
