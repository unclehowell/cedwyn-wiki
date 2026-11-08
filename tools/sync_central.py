#!/usr/bin/env python3
"""Fill this webapp's own data store, data/central.json, with only the central-catalogue fields the page shows.
Read-only against the central catalogue (https://cedwyn.bucklerfamily.estate/api/catalogue/<id>). data/central.json is a
derived cache: never edit it by hand; the central catalogue stays the single source of truth. The file is rewritten only
when a record it holds changed.
The legal wiki (/wiki/): the record IDs come from every wiki page and data file in the repo (*.html, *.json; theme assets under
_static/ and wp-content/ are skipped), so a record cited on a page later is picked up on the next run with no hand-kept list.
An ID the central catalogue answers 404 for is listed under not_in_central. A run where more than half of the reads fail for any
other reason (network, 5xx) leaves the store as it was. Run by .github/workflows/sync-central.yml every 6 hours. — Sion's Tab agent"""
import json, re, sys, time, datetime, pathlib, urllib.request, urllib.error
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
items, miss, failed = {}, [], []
for i in sorted(ids):
    try:
        req = urllib.request.Request(f'{API}{i}?cb={int(time.time())}', headers={'User-Agent': 'cedwyn-webapp-sync/1.0'})
        it = (json.load(urllib.request.urlopen(req, timeout=30)) or {}).get('item') or {}
        if it.get('id') == i: items[i] = {k: it.get(k) for k in FIELDS}
        else: miss.append(i)
    except urllib.error.HTTPError as e:
        (miss if e.code == 404 else failed).append(i)
    except Exception:
        failed.append(i)
    time.sleep(0.15)
if ids and len(failed) * 2 > len(ids):
    sys.exit(f'{len(failed)} of {len(ids)} reads failed (not 404); data/central.json left as it was')
prev = {}
try: prev = json.loads(OUT.read_text(encoding='utf-8'))
except Exception: pass
for i in failed:   # a record that could not be read this run keeps its last known entry
    if i in prev.get('items', {}): items[i] = prev['items'][i]
    elif i in prev.get('not_in_central', []): miss.append(i)
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
print('written', len(items), 'missing', len(miss), 'unread', len(failed))
