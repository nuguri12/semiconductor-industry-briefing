# Decisions

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
