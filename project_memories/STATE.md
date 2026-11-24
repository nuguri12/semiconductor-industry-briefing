# Project State

Last updated: 2026-11-24

## Objective

Build a daily briefing of semiconductor and automation-equipment industry news, then deliver it to the team after content rights, quality, schedule, and recipients are confirmed.

## Current Status

- `briefing/` collects GDELT DOC API metadata and MSIT press-release RSS independently, normalizes records, removes duplicate URLs, and preserves per-source status. One source failure does not erase the other source's results.
- DeepSearch was removed from runtime/configuration because the user prefers no-cost sources. NAVER remains deferred pending detailed rights confirmation.
- GDELT contributes discovery metadata only. RSS descriptions are included only when the item has explicit KOGL Type 1/Type 1 rights metadata; otherwise the record is title/link only. The code does not fetch article bodies or call an LLM.
- MOTIR press releases are a documented candidate source, but its exact RSS endpoint is not yet wired. OpenDART is listed as a later corporate-disclosure source, not a news feed.
- AI summarization, market indicators, CI, and scheduled production delivery are not implemented.
- SMTP preview and local delivery ledger exist. Actual sender configuration and inbox receipt are unverified. Recipient for the user-authorized test remains nuguri12@gmail.com.
- User prefers no-fee sources. GDELT dataset attribution does not establish publisher article rights. The item-level RSS rights marker still needs validation against actual feed payloads. No RSS feed/API collection run or email send was performed in this change.
- A proposed email structure is in `docs/email-template.md` and awaits user approval. No external email was sent.

## Validation

- Before this source change, `python -m unittest discover -s tests -v` passed 29 tests on 2026-11-24.
- Tests were not rerun for this change. `tests/test_sources.py` still refers to DeepSearch and needs updating.

## Next Actions

1. Update and run source tests for RSS/Atom parsing, explicit rights metadata, dates, duplicates, and independent failure behavior.
2. Inspect real MSIT RSS items to verify whether KOGL Type 1 appears in feed metadata. Until then, RSS descriptions stay excluded.
3. Verify the exact MOTIR RSS endpoint and decide whether to add its feed adapter.
4. Revisit NAVER permissions with the intended email/display flow; obtain email template approval and confirm recipients/schedule before delivery.
