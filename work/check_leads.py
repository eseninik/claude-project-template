"""
Check that all leads from Google Sheets exist in amoCRM.

Reads leads from the specified Google Sheet, then searches amoCRM
for each lead by phone number (primary) and email (fallback).
Uses parallel async requests for speed.

Usage:
    py -3 work/check_leads.py
"""

import asyncio
import json
import logging
import re
import sys
import time
from pathlib import Path

import aiohttp
import gspread
from google.oauth2.service_account import Credentials

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("check_leads")

# ── Config ───────────────────────────────────────────────────────────────────
SPREADSHEET_ID = "1muwHvFh3X7mHWUATUANFjERpd7c4BCfsMg-lrVqII3k"
SHEET_GID = 1370828899
CREDENTIALS_FILE = "credentials.json"

AMOCRM_DOMAIN = "migratoramocrm.amocrm.ru"
AMOCRM_BASE_URL = f"https://{AMOCRM_DOMAIN}/api/v4"
AMOCRM_CLIENT_ID = "02d3686d-5423-400b-8918-78ecfaf396ff"
AMOCRM_CLIENT_SECRET = "1dwSS8Sg6o15MFwfMk2Cs7F0zyDS1hCgGVQzTvyAKSuoRj86mETFEab6YuDP127p"
AMOCRM_REDIRECT_URI = "https://example.com"

# Token file - pre-populated from server, auto-refreshed

# Parallelism settings
MAX_CONCURRENT = 5  # amoCRM rate limit ~7 req/sec, keep safe margin
REQUEST_DELAY = 0.2  # seconds between requests per worker

# ── Token management ─────────────────────────────────────────────────────────
TOKEN_FILE = Path("work/amo_tokens.json")


def load_tokens() -> dict:
    """Load cached tokens from file."""
    if TOKEN_FILE.exists():
        data = json.loads(TOKEN_FILE.read_text())
        log.info("Loaded cached tokens, expires_at=%s", data.get("expires_at"))
        return data
    return {}


def save_tokens(data: dict):
    """Save tokens to cache file."""
    TOKEN_FILE.write_text(json.dumps(data, indent=2))
    log.info("Saved tokens to %s", TOKEN_FILE)


async def refresh_access_token(session: aiohttp.ClientSession) -> str:
    """Refresh amoCRM OAuth2 token, return access_token."""
    cached = load_tokens()
    if cached.get("access_token") and cached.get("expires_at", 0) > time.time():
        log.info("Using cached access token (valid for %.0f more seconds)",
                 cached["expires_at"] - time.time())
        return cached["access_token"]

    log.info("Refreshing amoCRM access token...")
    url = f"https://{AMOCRM_DOMAIN}/oauth2/access_token"
    payload = {
        "client_id": AMOCRM_CLIENT_ID,
        "client_secret": AMOCRM_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": cached.get("refresh_token"),
        "redirect_uri": AMOCRM_REDIRECT_URI,
    }

    async with session.post(url, json=payload) as resp:
        if resp.status != 200:
            body = await resp.text()
            log.error("Token refresh failed: %s %s", resp.status, body[:500])
            raise RuntimeError(f"Token refresh failed: {resp.status}")
        data = await resp.json()

    tokens = {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "expires_at": time.time() + data.get("expires_in", 86400) - 300,
    }
    save_tokens(tokens)
    log.info("Token refreshed successfully, valid for %s seconds", data.get("expires_in"))
    return tokens["access_token"]


# ── Phone normalization ──────────────────────────────────────────────────────
def normalize_phone(phone: str) -> str:
    """Strip all non-digits, normalize to consistent format for comparison."""
    digits = re.sub(r"[^\d]", "", phone)
    # Russian phones: convert 8 prefix to 7
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    # Add country code if missing (assume Russia for 10-digit)
    if len(digits) == 10:
        digits = "7" + digits
    return digits


def extract_search_phone(phone: str) -> str:
    """Extract digits suitable for amoCRM search query."""
    digits = normalize_phone(phone)
    # amoCRM search works best with last 10 digits
    if len(digits) >= 10:
        return digits[-10:]
    return digits


# ── Google Sheets reader ─────────────────────────────────────────────────────
def read_sheet_leads() -> list[dict]:
    """Read all leads from Google Sheet."""
    log.info("Connecting to Google Sheets...")
    creds = Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.get_worksheet_by_id(SHEET_GID)

    log.info("Reading sheet data...")
    rows = ws.get_all_values()
    headers = rows[0]
    leads = []

    for i, row in enumerate(rows[1:], start=2):
        if not any(row[:5]):  # skip empty rows
            continue
        lead = {
            "row": i,
            "created": row[0] if len(row) > 0 else "",
            "name": row[1] if len(row) > 1 else "",
            "email": row[2] if len(row) > 2 else "",
            "phone": row[3] if len(row) > 3 else "",
            "nick": row[4] if len(row) > 4 else "",
        }
        leads.append(lead)

    log.info("Read %d leads from sheet (headers: %s)", len(leads), headers[:5])
    return leads


# ── amoCRM search ────────────────────────────────────────────────────────────
async def search_amo_lead(
    session: aiohttp.ClientSession,
    access_token: str,
    query: str,
    semaphore: asyncio.Semaphore,
) -> list[dict]:
    """Search amoCRM leads by query string. Returns list of matching leads."""
    async with semaphore:
        await asyncio.sleep(REQUEST_DELAY)
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        url = f"{AMOCRM_BASE_URL}/leads"
        params = {"query": query, "limit": "10"}

        try:
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status == 204:
                    return []
                if resp.status == 429:
                    log.warning("Rate limited on query=%s, waiting 3s...", query)
                    await asyncio.sleep(3)
                    return await search_amo_lead(session, access_token, query, semaphore)
                if resp.status != 200:
                    body = await resp.text()
                    log.error("Search failed for query=%s: %s %s", query, resp.status, body[:200])
                    return []
                data = await resp.json()
                return data.get("_embedded", {}).get("leads", [])
        except Exception as e:
            log.error("Request error for query=%s: %s", query, e)
            return []


async def search_amo_contacts(
    session: aiohttp.ClientSession,
    access_token: str,
    query: str,
    semaphore: asyncio.Semaphore,
) -> list[dict]:
    """Search amoCRM contacts by query string."""
    async with semaphore:
        await asyncio.sleep(REQUEST_DELAY)
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        url = f"{AMOCRM_BASE_URL}/contacts"
        params = {"query": query, "limit": "10"}

        try:
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status == 204:
                    return []
                if resp.status == 429:
                    log.warning("Rate limited on contacts query=%s, waiting 3s...", query)
                    await asyncio.sleep(3)
                    return await search_amo_contacts(session, access_token, query, semaphore)
                if resp.status != 200:
                    body = await resp.text()
                    log.error("Contact search failed for query=%s: %s %s", query, resp.status, body[:200])
                    return []
                data = await resp.json()
                return data.get("_embedded", {}).get("contacts", [])
        except Exception as e:
            log.error("Contact request error for query=%s: %s", query, e)
            return []


async def check_single_lead(
    session: aiohttp.ClientSession,
    access_token: str,
    lead: dict,
    semaphore: asyncio.Semaphore,
) -> dict:
    """Check if a single lead exists in amoCRM. Returns result dict."""
    row = lead["row"]
    phone = lead["phone"].strip()
    email = lead["email"].strip()
    name = lead["name"].strip()
    nick = lead["nick"].strip()

    result = {
        "row": row,
        "name": name,
        "phone": phone,
        "email": email,
        "nick": nick,
        "created": lead["created"],
        "found": False,
        "found_by": None,
        "amo_lead_ids": [],
        "amo_lead_names": [],
        "search_attempts": [],
    }

    # Strategy 1: Search by phone (most reliable)
    if phone:
        search_phone = extract_search_phone(phone)
        if search_phone:
            leads_found = await search_amo_lead(session, access_token, search_phone, semaphore)
            result["search_attempts"].append(f"phone:{search_phone} -> {len(leads_found)} results")
            if leads_found:
                result["found"] = True
                result["found_by"] = "phone"
                result["amo_lead_ids"] = [l["id"] for l in leads_found]
                result["amo_lead_names"] = [l.get("name", "?") for l in leads_found]
                return result

    # Strategy 2: Search by email
    if email:
        leads_found = await search_amo_lead(session, access_token, email, semaphore)
        result["search_attempts"].append(f"email:{email} -> {len(leads_found)} results")
        if leads_found:
            result["found"] = True
            result["found_by"] = "email"
            result["amo_lead_ids"] = [l["id"] for l in leads_found]
            result["amo_lead_names"] = [l.get("name", "?") for l in leads_found]
            return result

    # Strategy 3: Search contacts by phone (lead might exist under contact)
    if phone:
        search_phone = extract_search_phone(phone)
        if search_phone:
            contacts = await search_amo_contacts(session, access_token, search_phone, semaphore)
            result["search_attempts"].append(f"contact_phone:{search_phone} -> {len(contacts)} results")
            if contacts:
                result["found"] = True
                result["found_by"] = "contact_phone"
                result["amo_lead_ids"] = [c["id"] for c in contacts]
                result["amo_lead_names"] = [c.get("name", "?") for c in contacts]
                return result

    # Strategy 4: Search contacts by email
    if email:
        contacts = await search_amo_contacts(session, access_token, email, semaphore)
        result["search_attempts"].append(f"contact_email:{email} -> {len(contacts)} results")
        if contacts:
            result["found"] = True
            result["found_by"] = "contact_email"
            result["amo_lead_ids"] = [c["id"] for c in contacts]
            result["amo_lead_names"] = [c.get("name", "?") for c in contacts]
            return result

    return result


# ── Main ─────────────────────────────────────────────────────────────────────
async def main():
    log.info("=== Lead Verification: Google Sheets -> amoCRM ===")
    start_time = time.time()

    # Step 1: Read sheet
    leads = read_sheet_leads()
    log.info("Loaded %d leads from Google Sheets", len(leads))

    # Step 2: Get amoCRM token
    async with aiohttp.ClientSession() as session:
        access_token = await refresh_access_token(session)
        log.info("amoCRM token ready")

        # Step 3: Check all leads in parallel
        semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        log.info("Starting parallel verification with %d workers...", MAX_CONCURRENT)

        tasks = [
            check_single_lead(session, access_token, lead, semaphore)
            for lead in leads
        ]

        results = []
        # Process in batches of 50 for progress reporting
        batch_size = 50
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            batch_results = await asyncio.gather(*batch)
            results.extend(batch_results)
            found_in_batch = sum(1 for r in batch_results if r["found"])
            log.info("Progress: %d/%d checked (%d found in this batch)",
                     len(results), len(tasks), found_in_batch)

    # Step 4: Analyze results
    elapsed = time.time() - start_time
    found = [r for r in results if r["found"]]
    not_found = [r for r in results if not r["found"]]

    log.info("=" * 60)
    log.info("VERIFICATION COMPLETE in %.1f seconds", elapsed)
    log.info("Total leads in sheet: %d", len(results))
    log.info("Found in amoCRM: %d (%.1f%%)", len(found), len(found) / len(results) * 100 if results else 0)
    log.info("NOT found in amoCRM: %d (%.1f%%)", len(not_found), len(not_found) / len(results) * 100 if results else 0)

    # Found by method breakdown
    by_method = {}
    for r in found:
        method = r["found_by"]
        by_method[method] = by_method.get(method, 0) + 1
    log.info("Found by method: %s", by_method)

    # Save detailed report
    report = {
        "summary": {
            "total": len(results),
            "found": len(found),
            "not_found": len(not_found),
            "found_pct": round(len(found) / len(results) * 100, 1) if results else 0,
            "by_method": by_method,
            "elapsed_seconds": round(elapsed, 1),
        },
        "not_found_leads": not_found,
        "found_leads": found,
    }

    report_path = Path("work/lead_verification_report.json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Full report saved to %s", report_path)

    # Print not-found leads for quick review
    if not_found:
        log.info("\n=== LEADS NOT FOUND IN AMOCRM ===")
        for r in not_found:
            log.info(
                "Row %d: %s | Phone: %s | Email: %s | Nick: %s | Attempts: %s",
                r["row"], r["name"], r["phone"], r["email"], r["nick"],
                "; ".join(r["search_attempts"]),
            )

    return report


if __name__ == "__main__":
    report = asyncio.run(main())
    # Exit code: 0 if all found, 1 if some missing
    sys.exit(0 if report["summary"]["not_found"] == 0 else 1)
