"""Check Google Drive link quality in amoCRM deals (Воронка pipeline, FM Done+)."""

import urllib.request, json, sys, re
from datetime import datetime, timezone

# Config
PIPELINE_ID = 7323650  # Воронка
TARGET_STATUS_IDS = [
    60973506,  # FM Done
    69052858,  # SS Paid
    66760510,  # SS Done
    79109214,  # Pre-paid (фулл позже 2 недели+)
    66910342,  # Pre-paid (Идет на фулл/внесен второй платеж)
]
FIELD_PERVICHKA = 1655003  # Запись первички ссылка
FIELD_SS = 1655005         # Запись СС ссылка

STATUS_NAMES = {
    60973506: 'FM Done',
    69052858: 'SS Paid',
    66760510: 'SS Done',
    79109214: 'Pre-paid (2 нед+)',
    66910342: 'Pre-paid (идет на фулл)',
}

# Read token
with open('/root/quality-control-bot/.env') as f:
    for line in f:
        if line.startswith('AMOCRM_ACCESS_TOKEN='):
            TOKEN = line.split('=', 1)[1].strip()
            break

BASE = 'https://migratoramocrm.amocrm.ru/api/v4'


def api_get(endpoint, params=None):
    url = BASE + endpoint
    if params:
        url += '?' + '&'.join(f'{k}={v}' for k, v in params.items())
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {TOKEN}'})
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())


def classify_link(url):
    """Classify a Google Drive link."""
    if not url or not url.strip():
        return 'EMPTY'

    url = url.strip()

    # Google Drive file patterns
    file_patterns = [
        r'drive\.google\.com/file/d/[a-zA-Z0-9_-]+',
        r'drive\.google\.com/open\?id=[a-zA-Z0-9_-]+',
        r'docs\.google\.com/.+/d/[a-zA-Z0-9_-]+',
    ]

    # Google Drive folder pattern
    folder_patterns = [
        r'drive\.google\.com/drive/folders/[a-zA-Z0-9_-]+',
        r'drive\.google\.com/drive/u/\d+/folders/[a-zA-Z0-9_-]+',
    ]

    for pat in file_patterns:
        if re.search(pat, url):
            return 'OK_FILE'

    for pat in folder_patterns:
        if re.search(pat, url):
            return 'FOLDER'

    if 'drive.google.com' in url or 'docs.google.com' in url:
        return 'GDRIVE_OTHER'

    return 'OTHER_URL'


def get_field_value(deal, field_id):
    """Extract custom field value from deal."""
    cfs = deal.get('custom_fields_values') or []
    for cf in cfs:
        if cf.get('field_id') == field_id:
            vals = cf.get('values', [])
            if vals:
                return vals[0].get('value', '')
    return ''


# Fetch all deals in target statuses
print(f'Fetching deals from Воронка (FM Done and later)...')
print(f'Timestamp: {datetime.now(timezone.utc).isoformat()}')
print()

all_deals = []
for status_id in TARGET_STATUS_IDS:
    page = 1
    while True:
        try:
            params = {
                'filter[statuses][0][pipeline_id]': str(PIPELINE_ID),
                'filter[statuses][0][status_id]': str(status_id),
                'limit': '50',
                'page': str(page),
            }
            data = api_get('/leads', params)
            leads = data.get('_embedded', {}).get('leads', [])
            if not leads:
                break
            for lead in leads:
                lead['_status_name'] = STATUS_NAMES.get(status_id, str(status_id))
            all_deals.extend(leads)
            print(f'  {STATUS_NAMES.get(status_id, status_id)}: page {page}, got {len(leads)} deals')
            if len(leads) < 50:
                break
            page += 1
        except urllib.error.HTTPError as e:
            if e.code == 204:
                print(f'  {STATUS_NAMES.get(status_id, status_id)}: 0 deals')
                break
            print(f'  Error fetching {status_id} page {page}: {e}')
            break
        except Exception as e:
            print(f'  Error fetching {status_id} page {page}: {e}')
            break

print(f'\nTotal deals fetched: {len(all_deals)}')
print()

# Analyze each deal
results = {
    'pervichka': {'OK_FILE': 0, 'FOLDER': 0, 'EMPTY': 0, 'GDRIVE_OTHER': 0, 'OTHER_URL': 0},
    'ss': {'OK_FILE': 0, 'FOLDER': 0, 'EMPTY': 0, 'GDRIVE_OTHER': 0, 'OTHER_URL': 0},
}

problems = []

for deal in all_deals:
    deal_id = deal['id']
    deal_name = deal.get('name', 'N/A')
    status_name = deal.get('_status_name', '?')

    pervichka_url = get_field_value(deal, FIELD_PERVICHKA)
    ss_url = get_field_value(deal, FIELD_SS)

    perv_class = classify_link(pervichka_url)
    ss_class = classify_link(ss_url)

    results['pervichka'][perv_class] = results['pervichka'].get(perv_class, 0) + 1
    results['ss'][ss_class] = results['ss'].get(ss_class, 0) + 1

    has_problem = False
    problem_details = []

    if perv_class != 'OK_FILE':
        has_problem = True
        problem_details.append(f'Первичка: {perv_class}')
        if pervichka_url:
            problem_details.append(f'  URL: {pervichka_url[:120]}')

    if ss_class != 'OK_FILE':
        # SS может быть пустым если сделка на FM Done (SS ещё не было)
        if status_name == 'FM Done' and ss_class == 'EMPTY':
            pass  # OK - SS ещё не проведена
        else:
            has_problem = True
            problem_details.append(f'СС: {ss_class}')
            if ss_url:
                problem_details.append(f'  URL: {ss_url[:120]}')

    if has_problem:
        problems.append({
            'id': deal_id,
            'name': deal_name,
            'status': status_name,
            'pervichka': perv_class,
            'pervichka_url': pervichka_url[:120] if pervichka_url else '',
            'ss': ss_class,
            'ss_url': ss_url[:120] if ss_url else '',
            'details': problem_details,
        })

# Print summary
print('=' * 70)
print('SUMMARY REPORT')
print('=' * 70)
print()
print('Запись первички ссылка:')
for k, v in sorted(results['pervichka'].items()):
    pct = v / len(all_deals) * 100 if all_deals else 0
    marker = ' OK ' if k == 'OK_FILE' else ' !!!'
    print(f'{marker} {k:>15}: {v:>4} ({pct:.1f}%)')

print()
print('Запись СС ссылка:')
for k, v in sorted(results['ss'].items()):
    pct = v / len(all_deals) * 100 if all_deals else 0
    marker = ' OK ' if k == 'OK_FILE' else ' !!!'
    print(f'{marker} {k:>15}: {v:>4} ({pct:.1f}%)')

print()
print(f'Total deals: {len(all_deals)}')
print(f'Deals with problems: {len(problems)}')
print()

# Print problem deals grouped by type
if problems:
    print('=' * 70)
    print('PROBLEM DEALS')
    print('=' * 70)

    # Group by problem type
    by_type = {}
    for p in problems:
        types = []
        if p['pervichka'] != 'OK_FILE':
            types.append(f"Первичка={p['pervichka']}")
        if p['ss'] != 'OK_FILE' and not (p['status'] == 'FM Done' and p['ss'] == 'EMPTY'):
            types.append(f"СС={p['ss']}")
        key = ' + '.join(types) if types else 'unknown'
        by_type.setdefault(key, []).append(p)

    for ptype, deals in sorted(by_type.items()):
        print(f'\n--- {ptype} ({len(deals)} deals) ---')
        for p in deals:
            print(f"  #{p['id']} | {p['name'][:45]:<45} | {p['status']}")
            if p['pervichka_url']:
                print(f"    Первичка URL: {p['pervichka_url']}")
            if p['ss_url']:
                print(f"    СС URL: {p['ss_url']}")

# Save JSON report
report = {
    'timestamp': datetime.now(timezone.utc).isoformat(),
    'pipeline': 'Воронка (7323650)',
    'total_deals': len(all_deals),
    'summary': results,
    'problems_count': len(problems),
    'problems': problems,
}

with open('/tmp/link_check_report.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print(f'\nFull JSON report: /tmp/link_check_report.json')
