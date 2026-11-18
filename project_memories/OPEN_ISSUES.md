# Open Issues

Only unresolved questions, risks, and follow-up investigations belong here. Remove or resolve items when their next action is complete.

## ISSUE-001 — Select free market-indicator sources

- **Status:** Open
- **Question:** Which no-fee sources provide the required FX rates and stock indexes under terms suitable for the internal digest?
- **Why it matters:** Market indicators are part of the requested briefing, but no source has been selected.
- **Next action:** Confirm required pairs and indexes; compare free API coverage, freshness, attribution, and internal-use restrictions.

## ISSUE-002 — Confirm news-content processing rights

- **Status:** Blocked for NAVER-to-GPT workflow; open for GDELT-linked publisher content.
- **Finding (2026-11-18):** NAVER API HUB Search API terms effective 2026-09-20 prohibit inputting search-result data into AI, processing/displaying altered results, and storing or distributing data outside narrow exceptions. GDELT permits use of its datasets with attribution, but that does not establish rights to full publisher articles.
- **Next action:** Obtain written NAVER permission for the intended internal GPT digest or choose a different Korean source with suitable rights. For GDELT, use metadata/links for discovery and verify publisher permissions before passing article text to GPT.
- **Sources:** https://www.ncloud.com/support/notice/all/2243 ; https://gdeltproject.org/about.html

## ISSUE-003 — Define news-query keywords

- **Status:** Deferred until keyword filtering is implemented
- **Question:** Which companies, technologies, and event types should the GDELT and NAVER queries cover?
- **Next action:** Ask the user when implementation reaches query configuration. Do not invent a list beforehand.

## ISSUE-004 — Choose schedule and delivery channel

- **Status:** Open
- **Question:** What morning run time and team destination should the service use?
- **Next action:** Confirm these before enabling scheduled production delivery.

## ISSUE-005 — Reconcile NAVER API HUB call-limit documentation

- **Status:** Open
- **Finding (2026-11-18):** The official overview says NAVER Search calls are combined and capped at 775,000 per month, not per day. The official News endpoint guide also says 25,000 calls per day. The service is temporarily free, with advance notice promised before paid conversion. No official source reviewed supports 75,000 free calls per day.
- **Next action:** Confirm effective daily and monthly limits in the NAVER API HUB console or with NAVER support before sizing production usage.
- **Sources:** https://guide.ncloud-docs.com/docs/apihub-overview ; https://api.ncloud-docs.com/docs/naver-api-hub-search-news ; https://guide.ncloud-docs.com/docs/apihub-spec
