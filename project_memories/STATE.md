# Project State

Last updated: 2026-11-26

## Objective

Build a daily briefing of semiconductor and automation-equipment industry news, then deliver it to the team after content rights, quality, schedule, and recipients are confirmed.

## Current Status

- `briefing/` collects GDELT DOC API metadata and MSIT press-release RSS independently, normalizes records, removes duplicate URLs, and preserves per-source status. One source failure does not erase the other source's results.
- DeepSearch was removed from runtime/configuration because the user prefers no-cost sources. NAVER remains deferred pending detailed rights confirmation.
- GDELT contributes discovery metadata only. RSS descriptions are included only when the item has explicit KOGL Type 1/Type 1 rights metadata; otherwise the record is title/link only. The code does not fetch article bodies or call an LLM.
- MOTIR press releases are a documented candidate source, but its exact RSS endpoint is not yet wired. OpenDART is listed as a later corporate-disclosure source, not a news feed.
- AI summarization, market indicators, CI, and scheduled production delivery are not implemented.
- SMTP preview and local delivery ledger exist. The live MSIT feed responded, but a live query for `(반도체 OR 장비)` over 72 hours returned no matching articles. GDELT returned HTTP 429 after its one retry. Do not send a partial or empty live collection.
- The MSIT feed uses `YYYY.MM.DD` publication dates. The adapter now parses that date format in addition to ISO/RFC dates. This confirms feed connectivity and parsing, but the sampled query did not find matching semiconductor/equipment items.
- A user-authorized SMTP test to `nuguri12@gmail.com` did not send: the delivery ledger records the test key as `failed`. Follow-up diagnostics confirmed EHLO and STARTTLS succeed and Gmail advertises LOGIN/PLAIN/XOAUTH2, but `smtplib.login()` is followed by a disconnect with no SMTP reply code. No message was accepted. SMTP host/port/sender settings match Gmail and the approved sender. The connected Gmail MCP profile resolves to the same account, so Gmail API access works independently of this project's password-based SMTP path. The exact server-side rejection reason remains unknown; do not retry the failed delivery key.
- User prefers no-fee sources. GDELT dataset attribution does not establish publisher article rights. The item-level RSS rights marker still needs validation against actual feed payloads.
- SMTP retest succeeded on 2026-11-26 at 14:53 KST after the user configured an app password. The existing CLI sent one synthetic fixture email to `nuguri12@gmail.com` with delivery ID `smtp-app-password-test-20261126-01`; exit code 0 and ledger status `sent`. The connected Gmail search independently confirmed the matching message in INBOX (message ID `1a2166a553c83cc2`). No Gmail API/OAuth implementation is needed for this verified SMTP path. The earlier disconnect's exact cause remains unproven.
- A proposed email structure is in `docs/email-template.md` and awaits user approval. Only the synthetic test email has been sent; live-news delivery and scheduling remain unverified.

## Validation

- The new MSIT dotted-date regression test failed before the parser change and passed after it.
- The full suite ran: 25 tests passed; five tests in the pre-existing, untracked `tests/test_sources.py` failed because they still expect the removed DeepSearch adapter/signature.

## Next Actions

1. Investigate GDELT HTTP 429 and collect a live sample when the endpoint permits requests.
2. Keep the verified SMTP/app-password path. Validate a live-news email after resolving collection issues; preserve existing delivery IDs to prevent duplicate test sends. Never paste credentials into chat.
3. Update `tests/test_sources.py` to match GDELT + MSIT RSS and rerun the full suite.
4. Inspect actual MSIT RSS rights metadata before including feed descriptions in email.
5. Verify the exact MOTIR RSS endpoint and decide whether to add its feed adapter.
6. Revisit NAVER permissions and confirm briefing content/schedule before routine delivery.
