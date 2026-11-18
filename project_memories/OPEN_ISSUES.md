# Open Issues

Only unresolved questions, risks, and follow-up investigations belong here. Remove or resolve items when their next action is complete.

## ISSUE-001 — Select free market-indicator sources

- **Status:** Open
- **Question:** Which no-fee sources provide the required FX rates and stock indexes under terms suitable for the internal digest?
- **Why it matters:** Market indicators are part of the requested briefing, but no source has been selected.
- **Next action:** Confirm required pairs and indexes; compare free API coverage, freshness, attribution, and internal-use restrictions.

## ISSUE-002 — Confirm news-content processing rights

- **Status:** Open
- **Question:** Which fields returned by GDELT and NAVER API HUB may be stored, sent to GPT, and included in an internal team digest?
- **Why it matters:** API access does not automatically authorize article-text reuse or redistribution.
- **Next action:** Review each provider's terms and limit ingestion to fields permitted for the intended use.

## ISSUE-003 — Define news-query keywords

- **Status:** Deferred until keyword filtering is implemented
- **Question:** Which companies, technologies, and event types should the GDELT and NAVER queries cover?
- **Next action:** Ask the user when implementation reaches query configuration. Do not invent a list beforehand.

## ISSUE-004 — Choose schedule and delivery channel

- **Status:** Open
- **Question:** What morning run time and team destination should the service use?
- **Next action:** Confirm these before enabling scheduled production delivery.
