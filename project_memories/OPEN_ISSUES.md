# Open Issues

## ISSUE-001 — RSS item rights and summaries

- **Status:** Open
- **Question:** Can the selected feed's descriptions be used in the internal email, and how is each item's KOGL Type 1 marking represented?
- **Current guard:** The collector uses a feed description only when an explicit KOGL Type 1 / Type 1 marker is present in RSS rights metadata. Otherwise it emits title and link only.
- **Next action:** Inspect actual MSIT feed items and verify how their rights markers are encoded before enabling summaries.
- **Source:** https://msit.go.kr/contents/cont.do?mId=161&mPid=147&sCode=user

## ISSUE-002 — GDELT-linked publisher rights

- **Status:** Open
- **Question:** What publisher article content, if any, may be sent to an LLM or redistributed?
- **Finding:** GDELT's dataset license does not confer rights to linked publishers' article text.
- **Next action:** Keep GDELT use to discovery metadata unless publisher rights are separately confirmed.
- **Source:** https://gdeltproject.org/about.html

## ISSUE-003 — NAVER API rights

- **Status:** Deferred by user
- **Question:** What are the exact permissions for displaying unmodified NAVER search results in an internal email, and what storage limits apply?
- **Next action:** Recheck current official terms and ask NAVER for written permission if the intended email workflow is not expressly covered. Do not call the API before then.
- **Source:** https://developers.naver.com/products/intro/terms/terms.md

## ISSUE-004 — MOTIR RSS endpoint

- **Status:** Open
- **Question:** What exact URL does the official Ministry of Trade, Industry and Resources RSS button serve?
- **Finding:** Its press-release board states KOGL Type 1; feed endpoint was not recovered during this change.
- **Next action:** Verify the exact RSS endpoint and test a fixture/live feed separately before enabling it.
- **Source:** https://www.motir.go.kr/kor/article/ATCL3f49a5a8c

## ISSUE-005 — Briefing content and delivery approval

- **Status:** Open
- **Question:** Is the email structure approved, and what recipient(s) and schedule should be used?
- **Next action:** Review `docs/email-template.md`; confirm recipient and send time before scheduled delivery.

## ISSUE-006 — Industry coverage quality

- **Status:** Open
- **Question:** Do GDELT and MSIT cover the desired semiconductor and automation-equipment topics with acceptable relevance and freshness?
- **Next action:** Run an authorized live sample and review relevance, duplicates, feed limits, and timestamps.

## ISSUE-007 — Market indicators

- **Status:** Open
- **Question:** Which FX rates and stock indexes should be included, and from which permitted sources?
- **Next action:** Confirm the instruments, then compare free APIs and their terms.
