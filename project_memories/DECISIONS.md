# Decisions

Record significant accepted choices with date, rationale, and impact. Keep unresolved questions in `OPEN_ISSUES.md`.

## DEC-001 — Use GDELT and NAVER API HUB as initial news sources

- **Date:** 2026-11-18
- **Decision:** Use GDELT for global news search and NAVER API HUB Search API for Korean news search. Add sources only when a demonstrated coverage need warrants it.
- **Rationale:** These are the selected starting sources; the design can expand later without committing to a larger source set now.
- **Impact:** GDELT remains the global discovery candidate. The NAVER API HUB client is on hold for the GPT digest because its current Search API terms conflict with the planned processing; resolve ISSUE-002 before implementation.

## DEC-002 — Prioritize no-fee data sources

- **Date:** 2026-11-18
- **Decision:** Prioritize sources with no access fee for news and market indicators.
- **Rationale:** Free access is the leading source-selection criterion.
- **Impact:** NAVER API HUB is temporarily free according to its current guide. Its overview states 775,000 combined Search calls per month, while the News endpoint guide still states 25,000 calls per day. Confirm which limits apply before production; usage rights remain a separate blocker (ISSUE-002).

## DEC-003 — Defer keyword selection until implementation needs it

- **Date:** 2026-11-18
- **Decision:** Do not set GDELT or NAVER query keywords yet. Ask the user when keyword filtering is about to be implemented.
- **Rationale:** The user explicitly requested control over the keyword scope.
- **Impact:** Keep query terms configurable and do not hard-code an assumed list.
