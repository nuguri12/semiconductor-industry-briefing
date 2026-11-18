# Project State

Last updated: 2026-11-18

## Objective

Build a daily morning briefing of overnight global news affecting the semiconductor and automation-equipment industries. Include relevant market indicators such as foreign-exchange rates and stock indexes, then deliver the briefing to the team.

## Current Status

- Planning stage. The README describes the proposed workflow; application code and CI have not been added.
- Initial news sources: GDELT for global coverage and NAVER API HUB Search API for Korean coverage. More sources may be added when a demonstrated coverage gap warrants it.
- Prefer no-fee sources. The reviewed NAVER pricing screenshot showed KRW 0 and a daily Search API limit of 25,000 calls; recheck pricing and quota before production.
- Query keywords are intentionally undecided. Ask the user when keyword filtering is about to be implemented.
- A free market-indicator source, schedule, delivery channel, and permitted content-processing scope remain undecided.

## Next Actions

1. Select free FX and index sources after confirming required instruments.
2. Review provider terms for processing and internal distribution.
3. Ask the user for query keywords when implementation reaches query configuration.
4. Confirm schedule and team destination before enabling scheduled delivery.
