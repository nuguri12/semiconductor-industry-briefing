# Project State

Last updated: 2026-11-20

## Objective

Build a daily morning briefing of overnight global news affecting the semiconductor and automation-equipment industries. Include relevant market indicators such as foreign-exchange rates and stock indexes, then deliver the briefing to the team.

## Current Status

- Requirements, architecture proposal and development plan are available in `docs/`. Implementation, CI, deployment and team delivery have not started.
- G1 documented the Korean workflow, data contracts, team benefit hypotheses and operating policies. G2 defined a conditional MVP stack and delivery recovery design. Benefits and operating costs have not been measured.
- Initial news sources: GDELT for global coverage and NAVER API HUB Search API for Korean coverage. More sources may be added when a demonstrated coverage gap warrants it.
- Prefer no-fee sources. The reviewed NAVER pricing screenshot showed KRW 0 and a daily Search API limit of 25,000 calls; recheck pricing and quota before production.
- Query keywords are intentionally undecided. Ask the user when keyword filtering is about to be implemented.
- A free market-indicator source, schedule, delivery channel, and permitted content-processing scope remain undecided.

## Next Actions

1. Start the offline briefing in [the development plan](../docs/development-plan.md) with synthetic inputs.
2. Resolve the applicable [open issues](OPEN_ISSUES.md) at each integration boundary.
3. Measure quality, cost and preparation time in dry-run before activating delivery.
