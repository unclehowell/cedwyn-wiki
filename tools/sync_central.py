#!/usr/bin/env python3
"""Fill this webapp's own data store, data/central.json, with only the central-catalogue fields the page shows.
Read-only against the central catalogue (https://cedwyn.bucklerfamily.estate/api/catalogue, read as paged list requests). data/central.json is a
derived cache: never edit it by hand; the central catalogue stays the single source of truth. The file is rewritten only
when a record it holds changed.
The legal wiki (/wiki/): the record IDs come from every wiki page and data file in the repo (*.html, *.json; theme assets under
_static/ and wp-content/ are skipped), so a record cited on a page later is picked up on the next run with no hand-kept list.
An ID the whole catalogue listing does not hold is listed under not_in_central. A run that cannot read the whole listing,
or finds fewer than half the records the store held, leaves the store as it was. Run by .github/workflows/sync-central.yml every 6 hours. — Sion's Tab agent"""
import json, re, sys, time, datetime, pathlib, urllib.request
ROOT = pathlib.Path(__file__).resolve().parent.parent
API = 'https://cedwyn.bucklerfamily.estate/api/catalogue/'
FIELDS = ('id', 'kind', 'title', 'date_display', 'date_sort', 'status', 'page')
NEEDS = ['**/*.html', '**/*.json']   # where this webapp's record IDs live (globs)
SKIP = ('.git/', '.github/', '_static/', 'wp-content/', 'wp-includes/')   # path prefixes never scanned
OUT = ROOT / 'data' / 'central.json'   # served at /wiki/data/central.json
ids = set()
for g in NEEDS:
    for f in sorted(ROOT.glob(g)):
        if not f.is_file() or f.resolve() == OUT.resolve(): continue   # never read the store itself
        if f.relative_to(ROOT).as_posix().startswith(SKIP): continue
        ids |= set(re.findall(r'\b(?:EV|MR|AR)-\d{4}\b', f.read_text(encoding='utf-8', errors='replace')))
items, miss, cat, total, off = {}, [], {}, None, 0
try:   # paged list reads (/api/catalogue?limit=500&offset=N, edge-cached), not one uncached request per ID (8 Nov 2026, D1 read load)
    while True:
        req = urllib.request.Request(f"{API.rstrip('/')}?limit=500&offset={off}", headers={'User-Agent': 'cedwyn-webapp-sync/1.1'})
        page = json.load(urllib.request.urlopen(req, timeout=60))
        rows = page.get('items') or []
        total = page.get('total', total)
        for it in rows:
            if it.get('id'): cat[it['id']] = {k: it.get(k) for k in FIELDS}
        off += len(rows)
        if not rows or (total is not None and off >= total): break
        time.sleep(1)
except Exception as e:
    sys.exit(f'catalogue listing could not be read ({e}); data/central.json left as it was')
if total is None or len(cat) < total:
    sys.exit(f'catalogue listing incomplete ({len(cat)} of {total}); data/central.json left as it was')
for i in sorted(ids):
    if i in cat: items[i] = cat[i]
    else: miss.append(i)   # an ID the whole listing does not hold is not in the central catalogue
prev = {}
try: prev = json.loads(OUT.read_text(encoding='utf-8'))
except Exception: pass
if len(items) < max(1, len(prev.get('items', {})) // 2):
    sys.exit(f'only {len(items)} of {len(ids)} records found; data/central.json left as it was')
miss = sorted(set(miss))
if prev.get('items') == items and prev.get('not_in_central') == miss:
    print('no change', len(items)); sys.exit(0)
doc = {
    'source': API.rstrip('/'),
    'note': "This webapp's own data store: the central-catalogue fields for the record IDs cited in "
            + 'the served files (' + ', '.join(NEEDS) + ')' + '. Derived and read-only; never edit by hand (tools/sync_central.py rewrites it).',
    'fields': list(FIELDS),
    'synced_utc': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    'count': len(items), 'not_in_central': miss, 'items': items}
OUT.parent.mkdir(parents=True, exist_ok=True)   # first run: data/ may not exist yet
OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print('written', len(items), 'missing', len(miss))
