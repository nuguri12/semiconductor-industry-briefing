# Decisions

Record significant accepted choices with date, rationale, and impact. Keep unresolved questions in `OPEN_ISSUES.md`.

## DEC-001 — Use GDELT and NAVER API HUB as initial news sources

- **Date:** 2026-11-18
- **Decision:** Use GDELT for global news search and NAVER API HUB Search API for Korean news search. Add sources only when a demonstrated coverage need warrants it.
- **Rationale:** These are the selected starting sources; the design can expand later without committing to a larger source set now.
- **Impact:** Implement independent clients that return a shared article format and report failures independently.

## DEC-002 — Prioritize no-fee data sources

- **Date:** 2026-11-18
- **Decision:** Prioritize sources with no access fee for news and market indicators.
- **Rationale:** Free access is the leading source-selection criterion.
- **Impact:** Verify current pricing, quota, and usage rights before production. The reviewed NAVER API HUB screenshot showed KRW 0 and a daily Search API limit of 25,000 calls; this may change.

## DEC-003 — Defer keyword selection until implementation needs it

- **Date:** 2026-11-18
- **Decision:** Do not set GDELT or NAVER query keywords yet. Ask the user when keyword filtering is about to be implemented.
- **Rationale:** The user explicitly requested control over the keyword scope.
- **Impact:** Keep query terms configurable and do not hard-code an assumed list.
