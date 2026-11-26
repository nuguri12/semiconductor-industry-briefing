# Decisions

## DEC-014 — Try GitHub scheduling before Cloudflare (2026-11-27)

- **Decision:** User chose GitHub Actions schedule first, retaining workflow_dispatch for manual runs. Cloudflare migration is conditional on observed timing/missed-run problems, superseding DEC-013's immediate external-trigger proposal. Supabase Free remains selected.
- **Impact:** Measure expected time, workflow creation, job start and delivery completion separately. Preserve fixed window/run keys across retries. Diagnose schedule delay versus runner queue delay before choosing the remedy. Disable the old schedule before any future Cloudflare cutover. No deployment in this checkpoint.

## DEC-013 — Supabase selected; external trigger proposed (2026-11-27)

- **Decision:** User chose Supabase Free, superseding the Neon provider proposal. Reuse PostgreSQL schema/psycopg; prefer session pooler for IPv4 and verify TLS/role permissions.
- **Scheduling proposal:** Cloudflare Cron invokes GitHub workflow_dispatch; GitHub runs the existing Python/SMTP workload. User reported unreliable timing from GitHub schedule. Remove that scheduler dependency, but retain explicit awareness of runner queue delays.
- **Impact:** Prepare fixed scheduled window/run keys, execution-start/completion checks and duplicate-safe retries. No cloud resources or triggers deployed yet. Exact trigger time and tolerated delivery delay remain operational settings to confirm.

## DEC-012 — MOTIR activation and explicit PostgreSQL preparation (2026-11-26)

- **Decision:** Add MOTIR official empty-POST RSS as the third default collector using the shared RSS parser. Retain metadata-only output, independent source failures and URL deduplication. NIST feeds are live-reviewed candidates, not enabled sources.
- **Reason:** User requested more sources; MOTIR supplied a current relevant article when the two original sources did not. Preview and actual email receipt were verified without widening the 24h window.
- **Impact:** Local MVP is complete with the GDELT failure limitation. PostgreSQL is opt-in via `--store-db` and versioned input; no Neon resources exist yet per the user. Current schema covers manual snapshot storage only; fixed schedule windows, SQLite import and backup remain pending. Never treat mocked DB tests as real SQL verification.

## DEC-011 — Detailed hosted DB proposal (2026-11-26)

- **Proposal, not provisioned:** Neon Free PostgreSQL in AWS Singapore; GitHub Actions runs the existing Python collector and SMTP sender. See `docs/system-architecture.md` DB execution plan for schema, roles, migration, replay, backup and rollout checks.
- **Reason:** Existing PostgreSQL design and standard Python connection; Supabase remains a compatible alternative, while D1 requires HTTP access adaptation. No existing psycopg integration is claimed.
- **Impact:** Three business tables (runs, briefings, deliveries), immutable saved briefing, atomic delivery claim, no SQLite fallback on cloud DB failure. Account ownership, data location constraints and live receipt checks precede activation. Schedule and retention values are proposals, not user-approved operating settings.

## DEC-010 — Replay validated normalized snapshots (2026-11-26)

- **Decision:** JSON output uses schema version 1. `--input` replays validated snapshots without replacing source states, timestamps, query, ordering or date precision; legacy GDELT fixtures remain supported. Snapshot input preserves its selection instead of applying the CLI limit again.
- **Reason:** Preview and send must use the same live collection. The old input path reinterpreted normalized records as GDELT fixtures and lost provenance.
- **Impact:** Capture live JSON once and reuse it for preview/send with a stable delivery ID. Unsupported versions and malformed snapshots are rejected. Source counts and sanitized error classes/HTTP codes remain in saved output. No new dependencies or delivery infrastructure.

## DEC-009 — Local MVP acceptance criteria (2026-11-26)

- **Decision:** Use M1–M6 in `docs/development-plan.md` as the local MVP completion checklist: live collection, normalized relevant records, no-send preview, receipt of the same live articles, duplicate prevention, and failure handling.
- **Reason:** Synthetic email delivery proves transport but not the requested live-news workflow. Existing local scope excludes summaries and production scheduling.
- **Impact:** A failed source can remain an explicit limitation if the other source supplies valid articles and all acceptance checks pass. No valid live articles means incomplete. Preserve unresolved source errors; do not claim both sources work from a partial run. This local scope excludes RSS descriptions regardless of rights markers, superseding the description allowance in DEC-008 for this MVP.

## DEC-008 — Use free sources with separate rights boundaries (2026-11-24)

- **Decision:** Use GDELT for global article discovery and MSIT press-release RSS for Korean science/ICT/semiconductor policy. Exclude DeepSearch. Defer NAVER until its exact permissions are confirmed. Keep MOTIR RSS and OpenDART on the candidate list; activate only after endpoint/terms review.
- **Rationale:** Prioritize no-fee sources whose access and item rights can be checked; do not assume an RSS/API grants article-body or AI-summary rights.
- **Impact:** GDELT items remain title/link discovery records. RSS descriptions are included only when an item explicitly indicates KOGL Type 1. AI article summarization remains unimplemented.

## DEC-006 — Collection test terms (2026-11-21)

- User specified Infineon, ASE, HYUNDAI and MOBIS for the initial test.
- Queries remain explicit CLI inputs. Operational scope and ambiguous-name relevance remain open.
- User requested local message normalization first and GPT integration later.

## DEC-005 — Prefer free infrastructure (2026-11-20)

- User reiterated free-service priority, including DB hosting.
- Evaluate database, execution, monitoring and backup within free allowances. Obtain approval for paid upgrades.
- Neon Free remains a conditional recommendation. Compare Supabase Free and Cloudflare D1 with documented limits and operating effort. Measure actual usage before activation. Model API cost remains a separate budget.

Record significant accepted choices with date, rationale, and impact. Keep unresolved questions in `OPEN_ISSUES.md`.

## DEC-001 — Use GDELT and NAVER API HUB as initial news sources

- **Date:** 2026-11-18
- **Decision:** Use GDELT for global news search and NAVER API HUB Search API for Korean news search. Add sources only when a demonstrated coverage need warrants it.
- **Rationale:** These are the selected starting sources; the design can expand later without committing to a larger source set now.
- **Impact:** Superseded by DEC-008. GDELT remains in use; NAVER is deferred until exact permissions for the intended email workflow are verified.

## DEC-002 — Prioritize no-fee data sources

- **Date:** 2026-11-18
- **Decision:** Prioritize sources with no access fee for news and market indicators.
- **Rationale:** Free access is the leading source-selection criterion.
- **Impact:** Historical 2026-11-18 price/quota notes are not relied on for the current source selection. Current pricing and limits must be checked from official pages before adopting any API. Usage rights remain a separate gate.

## DEC-003 — Defer keyword selection until implementation needs it

- **Date:** 2026-11-18
- **Decision:** Do not hard-code GDELT or RSS query keywords. Keep each run's query as an explicit CLI input.
- **Rationale:** The user explicitly requested control over the keyword scope.
- **Impact:** Keep query terms configurable and do not hard-code an assumed list. This supersedes the earlier keyword deferral.

## DEC-004 — Minimize routine user intervention (2026-11-20)

- **Decision:** After review of policy, rights, sample output and dry-run results, obtain activation approval once. Apply the approved configuration automatically during normal runs.
- **Reason and alternative:** Daily manual release would repeat the same review and undermine the morning briefing's purpose.
- **Impact:** Record configuration changes. Reassess changes to approved scope and surface actionable exceptions. Notification thresholds, recipient and channel remain open.
