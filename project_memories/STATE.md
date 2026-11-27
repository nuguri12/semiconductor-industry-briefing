# Project State

Last updated: 2026-11-27

## Objective

Build a daily briefing of semiconductor and automation-equipment industry news, then deliver it to the team after content rights, quality, schedule, and recipients are confirmed.

## Current Status

- Review fixes (2026-11-27): invalid_records now fails before completion/delivery; job-owned artifacts are cleared before reruns (including Actions input failures); replay uses validated run_key identity while preserving the original saved plan/body. Different queries still fail closed. 74 tests: 69 passed, 5 real-DB checks skipped; actionlint passed. Output directories must not be shared by concurrent processes.

- Latest 2026-11-27: implemented fixed-window `briefing.schedule` / `briefing.job`, explicit GDELT absolute time parameters, shared RSS cutoff, scheduled DB claim/replay (migration 002), and GitHub Actions dry-run workflow. No Supabase connection, SMTP send, remote workflow execution or schedule activation in this iteration.
- Validation: 70 tests discovered, 65 passed, 5 real-PostgreSQL tests skipped. actionlint v1.7.12 passed. Manual historical-slot live dry-run yielded MOTIR 1 article, MSIT 0, GDELT 429; date-only overlap is explicitly disclosed. Evidence and caveats: `docs/scheduled-run.md`.
- Next: configure Supabase and run real migration/permission/concurrency checks; test Actions manually on GitHub; migrate existing delivery history before cloud send. Backup/retention and missing-run monitoring remain pending. Workflow schedule is opt-in via repository variable; never equate a disabled dry-run workflow with deployed production scheduling.

- 2026-11-27 provider decision: user chose Supabase Free instead of Neon. Existing PostgreSQL code is portable; Supabase TLS/session-pooler/roles remain unverified. Latest user decision: try GitHub Actions schedule first with workflow_dispatch for manual runs; migrate the trigger to Cloudflare only if observed timing or missed-run problems warrant it. Fixed scheduled-window keys and execution reports are implemented; independent missing-run monitoring remains pending. Runner queue delays require separate diagnosis. See latest section of `docs/database-setup.md`; older Neon references below are historical.

- Latest follow-up (2026-11-26): MOTIR official POST RSS is now the third active source. A current semiconductor-policy article passed preview, SMTP send and Gmail INBOX full-body/link verification. Stable key `mvp-live-motir-20261126-01` replay left the ledger unchanged and search still returned one message. Local M1–M6 are complete with the GDELT failure limitation; earlier blocked entries below are historical.
- PostgreSQL migration, versioned snapshot store and ledger are implemented behind explicit `--store-db`. The user confirmed no Neon project exists yet. Cloud SQL/TLS/roles/concurrency remain unverified; no cloud resources or scheduled jobs were created. See `docs/database-setup.md`.
- Latest tests: 49 discovered, 46 passed, 3 PostgreSQL integration checks skipped due to absent isolated test URL. NIST manufacturing/electronics feeds each returned 40 entries in review; they remain candidates (events/duplicates and English terms need selection rules).

- `briefing/` collects GDELT DOC API metadata and MSIT press-release RSS independently, normalizes records, removes duplicate URLs, and preserves per-source status. One source failure does not erase the other source's results.
- DeepSearch was removed from runtime/configuration because the user prefers no-cost sources. NAVER remains deferred pending detailed rights confirmation.
- GDELT contributes discovery metadata only. The local MVP omits RSS descriptions even when rights markers exist. The code does not fetch article bodies or call an LLM.
- MOTIR endpoint is `https://www.motir.go.kr/kor/article/ATCL3f49a5a8c/rss` (empty POST). OpenDART remains a corporate-disclosure candidate, not a news feed.
- AI summarization, market indicators and scheduled production delivery are not implemented. A locally validated GitHub Actions dry-run workflow is ready for hosted verification.
- SMTP preview and local delivery ledger exist. The live MSIT feed responded, but a live query for `(반도체 OR 장비)` over 72 hours returned no matching articles. GDELT returned HTTP 429 after its one retry. The CLI permits sending valid results from a partial collection, but blocks an empty result.
- The MSIT feed uses `YYYY.MM.DD` publication dates. The adapter now parses that date format in addition to ISO/RFC dates. This confirms feed connectivity and parsing, but the sampled query did not find matching semiconductor/equipment items.
- A user-authorized SMTP test to `nuguri12@gmail.com` did not send: the delivery ledger records the test key as `failed`. Follow-up diagnostics confirmed EHLO and STARTTLS succeed and Gmail advertises LOGIN/PLAIN/XOAUTH2, but `smtplib.login()` is followed by a disconnect with no SMTP reply code. No message was accepted. SMTP host/port/sender settings match Gmail and the approved sender. The connected Gmail MCP profile resolves to the same account, so Gmail API access works independently of this project's password-based SMTP path. The exact server-side rejection reason remains unknown; do not retry the failed delivery key.
- User prefers no-fee sources. GDELT dataset attribution does not establish publisher article rights. The item-level RSS rights marker still needs validation against actual feed payloads.
- SMTP test using the configured app-password path succeeded again on 2026-11-26. The current CLI sent one synthetic fixture email to `nuguri12@gmail.com` with delivery ID `mvp-smtp-test-20261126-01`; exit code 0 and ledger status `sent`. Gmail search found the matching message with subject `[산업 브리핑] 2026-11-26`. The earlier authentication disconnect cause remains unproven.
- `--email-check` passed on the same fixture and did not send. The current email format is recorded in `docs/email-template.md`; it remains a prototype pending content/schedule approval. Live-news delivery and scheduling remain unverified.

## Validation

- Latest run (2026-11-26): 37 tests passed. Snapshot replay preserves source states, collection time, query and publication precision; invalid snapshots fail closed. Conflicting send/preview flags are rejected.
- Live corporate 24h and Korean industry 24h/72h queries yielded GDELT HTTP 429 and healthy MSIT responses with zero matching articles. Inspection of 50 feed metadata entries found the sole matching semiconductor item dated November 20, outside the allowed window.
- Actual empty-result snapshot roundtrip was identical, preview exited 0, send gate exited 2, and the delivery ledger hash stayed unchanged. No live email was sent in this run. M1 remains blocked; live M2–M5 remain pending. M6 and mocked delivery safeguards passed. Evidence: ignored `output/mvp-20261126/`; report: `docs/collection-test.md`.

- The new MSIT dotted-date regression test failed before the parser change and passed after it.
- The current full suite passed: `python -m unittest discover -s tests -v` ran 32 tests successfully.
- Offline dry-run passed: `python -m briefing --input tests/fixtures/articles.json --email-check --to nuguri12@gmail.com` printed validation success and a preview without sending.

## Next Actions

1. Investigate GDELT HTTP 429 and collect a live sample when the endpoint permits requests.
2. Keep the verified SMTP/app-password path and the successful live MOTIR delivery ID. Do not resend that test or migrate it to a new empty ledger without importing history. Never paste credentials into chat.
3. Keep RSS descriptions excluded from the local MVP. Rights review applies only to a future scope extension.
4. Configure an isolated Supabase test database when the user is ready, then run the five PostgreSQL integration tests and role checks before cloud sending. Review NIST filtering and enterprise press-feed permissions before further source activation.
5. Revisit NAVER permissions and confirm the production email content and schedule before routine delivery.
