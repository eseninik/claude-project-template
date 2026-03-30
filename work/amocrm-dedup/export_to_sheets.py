"""
Export merged deals to Google Sheets — simple format with clickable URLs.
Single sheet, 3 columns: Username, Old deals, New deals (closed).
"""

import csv
import os
import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1-XuPgLcKhfcbFxSDFAUSmyRSNZk7sRaegiBQWYhZ5OE/edit"
CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "credentials.json")
MERGED_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "merged_deals_report.csv")

LEAD_URL = "https://migratoramocrm.amocrm.ru/leads/detail/"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def ids_to_urls(ids_str: str) -> str:
    """Convert semicolon-separated IDs to newline-separated URLs."""
    if not ids_str or not ids_str.strip():
        return "нет сделки"
    ids = [x.strip() for x in ids_str.split(";") if x.strip()]
    return "\n".join(f"{LEAD_URL}{lid}" for lid in ids)


def main():
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_url(SPREADSHEET_URL)
    print(f"Opened: {spreadsheet.title}")

    # Delete extra sheets (keep only first)
    worksheets = spreadsheet.worksheets()
    for ws in worksheets[1:]:
        spreadsheet.del_worksheet(ws)
        print(f"  Deleted sheet: {ws.title}")

    # Setup main sheet
    sheet = spreadsheet.sheet1
    sheet.update_title("Объединённые сделки")
    sheet.clear()

    # Read CSV
    with open(MERGED_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Build data: Username, Old deals (URLs), New deals closed (URLs)
    headers = ["Username", "Старые сделки", "Новые сделки (закрыты как Double)"]

    data = [headers]
    for r in rows:
        data.append([
            r["username"],
            ids_to_urls(r["old_lead_ids"]),
            ids_to_urls(r["new_lead_ids"]),
        ])

    sheet.update(range_name="A1", values=data)

    # Format header
    sheet.format("A1:C1", {
        "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 0.2},
        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
        "horizontalAlignment": "CENTER",
    })

    # Wrap text for URL cells
    sheet.format(f"A2:C{len(data)}", {
        "wrapStrategy": "WRAP",
    })

    # Column widths
    requests = [{
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet.id,
                "dimension": "COLUMNS",
                "startIndex": i,
                "endIndex": i + 1,
            },
            "properties": {"pixelSize": width},
            "fields": "pixelSize",
        }
    } for i, width in enumerate([200, 420, 420])]
    spreadsheet.batch_update({"requests": requests})

    print(f"  Written {len(rows)} rows")
    print(f"\nDone! {SPREADSHEET_URL}")


if __name__ == "__main__":
    main()
