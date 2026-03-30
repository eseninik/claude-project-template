"""
Update Google Sheet: add amoCRM links column and highlight not-found rows in red.

Usage:
    py -3 work/update_sheet.py
"""

import json
import logging
import sys
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials
from gspread.utils import rowcol_to_a1

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("update_sheet")

# ── Config ───────────────────────────────────────────────────────────────────
SPREADSHEET_ID = "1muwHvFh3X7mHWUATUANFjERpd7c4BCfsMg-lrVqII3k"
SHEET_GID = 1370828899
CREDENTIALS_FILE = "credentials.json"
REPORT_FILE = Path("work/lead_verification_report.json")
AMOCRM_DOMAIN = "migratoramocrm.amocrm.ru"
LINK_COL = 49  # Column AW (next after 48 existing)


def main():
    log.info("Loading verification report...")
    report = json.loads(REPORT_FILE.read_text(encoding="utf-8"))

    # Build row -> lead_id mapping
    row_to_ids = {}
    not_found_rows = set()

    for lead in report["found_leads"]:
        row = lead["row"]
        ids = lead.get("amo_lead_ids", [])
        if ids:
            row_to_ids[row] = ids[0]  # first match

    for lead in report["not_found_leads"]:
        not_found_rows.add(lead["row"])

    log.info("Found leads with IDs: %d, not found rows: %s", len(row_to_ids), not_found_rows)

    # Connect to Google Sheets
    log.info("Connecting to Google Sheets (write mode)...")
    creds = Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.get_worksheet_by_id(SHEET_GID)

    # Step 1: Write header
    log.info("Writing header 'amoCRM Link' to column %d...", LINK_COL)
    ws.update_cell(1, LINK_COL, "amoCRM_link")

    # Step 2: Prepare all cell values (hyperlinks)
    log.info("Preparing amoCRM links for %d rows...", len(row_to_ids) + len(not_found_rows))
    cells = []
    total_rows = report["summary"]["total"]

    for row_num in range(2, total_rows + 2):  # data starts at row 2
        lead_id = row_to_ids.get(row_num)
        if lead_id:
            url = f"https://{AMOCRM_DOMAIN}/leads/detail/{lead_id}"
            cells.append(url)
        elif row_num in not_found_rows:
            cells.append("NOT FOUND")
        else:
            cells.append("")

    # Batch update the link column
    log.info("Writing %d cells to column %d...", len(cells), LINK_COL)
    col_letter = gspread.utils.rowcol_to_a1(1, LINK_COL).rstrip("0123456789")
    cell_range = f"{col_letter}2:{col_letter}{total_rows + 1}"
    # Convert to list of lists for batch update
    ws.update(cell_range, [[c] for c in cells])
    log.info("Links written successfully")

    # Step 3: Highlight not-found rows in red
    if not_found_rows:
        log.info("Highlighting %d not-found rows in red...", len(not_found_rows))
        red_bg = {
            "backgroundColor": {
                "red": 1.0,
                "green": 0.8,
                "blue": 0.8,
                "alpha": 1.0,
            }
        }

        requests = []
        for row_num in sorted(not_found_rows):
            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": SHEET_GID,
                        "startRowIndex": row_num - 1,  # 0-indexed
                        "endRowIndex": row_num,
                        "startColumnIndex": 0,
                        "endColumnIndex": LINK_COL,
                    },
                    "cell": {
                        "userEnteredFormat": red_bg,
                    },
                    "fields": "userEnteredFormat.backgroundColor",
                }
            })

        sh.batch_update({"requests": requests})
        log.info("Red highlighting applied to rows: %s", sorted(not_found_rows))

    log.info("=== DONE === Sheet updated with %d amoCRM links, %d rows highlighted red",
             len(row_to_ids), len(not_found_rows))


if __name__ == "__main__":
    main()
