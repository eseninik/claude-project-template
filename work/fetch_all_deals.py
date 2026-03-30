"""Fetch ALL deals (FM Done+) with field values and save full data for Excel."""

import urllib.request, json, re
from datetime import datetime, timezone

PIPELINE_ID = 7323650
TARGET_STATUS_IDS = [60973506, 69052858, 66760510, 79109214, 66910342]
FIELD_PERVICHKA = 1655003
FIELD_SS = 1655005

STATUS_NAMES = {
    60973506: 'FM Done',
    69052858: 'SS Paid',
    66760510: 'SS Done',
    79109214: 'Pre-paid (2 нед+)',
    66910342: 'Pre-paid (идет на фулл)',
}

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
    return json.loads(urllib.request.urlopen(req).read())


def classify_link(url):
    if not url or not url.strip():
        return 'EMPTY'
    url = url.strip()
    file_pats = [
        r'drive\.google\.com/file/d/[a-zA-Z0-9_-]+',
        r'drive\.google\.com/open\?id=[a-zA-Z0-9_-]+',
        r'docs\.google\.com/.+/d/[a-zA-Z0-9_-]+',
    ]
    folder_pats = [
        r'drive\.google\.com/drive/folders/[a-zA-Z0-9_-]+',
        r'drive\.google\.com/drive/u/\d+/folders/[a-zA-Z0-9_-]+',
    ]
    for pat in file_pats:
        if re.search(pat, url):
            return 'OK_FILE'
    for pat in folder_pats:
        if re.search(pat, url):
            return 'FOLDER'
    if 'drive.google.com' in url or 'docs.google.com' in url:
        return 'GDRIVE_OTHER'
    return 'OTHER_URL'


def get_field_value(deal, field_id):
    cfs = deal.get('custom_fields_values') or []
    for cf in cfs:
        if cf.get('field_id') == field_id:
            vals = cf.get('values', [])
            if vals:
                return vals[0].get('value', '')
    return ''


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
            if len(leads) < 50:
                break
            page += 1
        except Exception:
            break

result = []
for deal in all_deals:
    perv_url = get_field_value(deal, FIELD_PERVICHKA)
    ss_url = get_field_value(deal, FIELD_SS)
    result.append({
        'id': deal['id'],
        'name': deal.get('name', ''),
        'status': deal['_status_name'],
        'responsible_user_id': deal.get('responsible_user_id', ''),
        'pervichka_url': perv_url,
        'pervichka_class': classify_link(perv_url),
        'ss_url': ss_url,
        'ss_class': classify_link(ss_url),
    })

with open('/tmp/all_deals_full.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f'Total: {len(result)} deals')
print(json.dumps({'ok_perv': sum(1 for d in result if d["pervichka_class"]=="OK_FILE"),
                   'ok_ss': sum(1 for d in result if d["ss_class"]=="OK_FILE"),
                   'total': len(result)}))
