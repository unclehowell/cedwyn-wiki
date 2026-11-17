# Legacy Wiki to central catalogue migration

This folder records the audited migration map from `greathousefarmwiki.wordpress.com` and the `/wiki/` mirror to the canonical record pages in `/catalogue/`.

`legacy-wiki-crosswalk.json` is a point-in-time audit generated 17 November 2026 from:

- the published WordPress Pages API inventory;
- the current central `core_items` register read-only snapshot;
- the current `unclehowell/cedwyn-wiki` main-branch file tree.

## How to read it

- `pages` contains every published legacy WordPress page and its classification.
- `routes` maps only pages safely matched to an existing central record (or to the kept ID where the legacy entry is withdrawn as a duplicate).
- `unresolved_record` means a page looks like a record but no safe central mapping was found.
- `id_collision` means the old identifier has been reused by a different central record; it must not be redirected until a new canonical ID is assigned.
- Narrative pages and multi-record indexes are not individual artifacts and must not be fabricated as catalogue records.

## Known exceptions

- Legacy EV-0607 and EV-0608 are ITV footage catalogue leads from 28 October 2026; the same IDs are already held by distinct 25 October 2026 analysis charts in the central catalogue. Neither record is overwritten.
- EV-0900 is present in the Wiki archive but absent from this central snapshot; it is a research synthesis and needs classification before any new catalogue entry.
- EV-0295 is a multi-record disclosure index, not a single evidence item.

## Deployment

The crosswalk is not itself a live redirect. `legacy-wiki-redirects.json` is the compact route map for the apex Worker: it contains only the 679 supported record destinations. The Worker should issue 301 redirects for those routes. Unmapped, conflicting, and narrative pages must remain accessible until reviewed. The 17 November snapshot classifies 679 published pages as catalogue records, 2 as ID collisions, 1 as an unresolved record, 30 as narrative/index pages under the evidence sections, and 262 as other narrative pages.

Central record writes remain add-only and must go through the designated catalogue writer. The public `/api/catalogue` endpoint is read-only.

Tracking issue: https://github.com/unclehowell/cedwyn/issues/611
