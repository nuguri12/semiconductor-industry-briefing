# Project State

Last updated: 2026-11-20

## Objective

Build a daily morning briefing of overnight global news affecting the semiconductor and automation-equipment industries. Include relevant market indicators such as foreign-exchange rates and stock indexes, then deliver the briefing to the team.

## Current Status

- Requirements, architecture proposal and development plan are available in `docs/`. Implementation, CI, deployment and team delivery have not started.
- G1 documented the Korean workflow, data contracts, team benefit hypotheses and operating policies. G2 defined a conditional MVP stack and delivery recovery design. Benefits and operating costs have not been measured.
- Initial news sources: GDELT for global coverage and NAVER API HUB Search API for Korean coverage. More sources may be added when a demonstrated coverage gap warrants it.
- Prefer no-fee sources. NAVER API HUB is temporarily free as of 2026-11-18; its overview states a combined NAVER Search limit of 775,000 calls per month, while its News endpoint guide still says 25,000 calls per day. The user-reported 75,000 free calls per day is not supported by the official pages reviewed. Resolve the documentation conflict with NAVER before relying on the limit.
- Query keywords are intentionally undecided. Ask the user when keyword filtering is about to be implemented.
- A free market-indicator source, schedule, delivery channel, and permitted content-processing scope remain undecided.
- Source review (2026-11-18): GDELT DOC 2.0 is suitable as a global discovery feed, subject to article-publisher rights and a live quality test. NAVER API HUB News Search is technically suitable for Korean discovery, but its Search API terms prohibit feeding results to AI and exposing processed results. Do not connect it to the planned GPT digest without written permission or a compliant redesign.

## Next Actions

1. Start the offline briefing in [the development plan](../docs/development-plan.md) with synthetic inputs.
2. Resolve the applicable [open issues](OPEN_ISSUES.md) at each integration boundary.
3. Measure quality, cost and preparation time in dry-run before activating delivery.

4. Select free FX and index sources after confirming required instruments.
5. Resolve the NAVER API HUB terms conflict before implementing Korean-news ingestion; verify publisher rights for any article text used with GPT.
6. Ask the user for query keywords when implementation reaches query configuration.
7. Confirm schedule and team destination before enabling scheduled delivery.
