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

## ISSUE-008 — GDELT rate limit during live sample

- **Status:** Open
- **Finding:** Two live collection attempts returned HTTP 429 after the adapter's single retry; no GDELT articles were collected.
- **Impact:** The current send gate blocks partial and empty live results, so a live-source briefing cannot be sent until GDELT responds successfully.
- **Next action:** Retry a live sample later at a lower request frequency and inspect GDELT response guidance if 429 persists.

## ISSUE-009 — Gmail SMTP authentication

- **Status:** Open
- **Finding:** EHLO and STARTTLS succeed; Gmail advertises LOGIN, PLAIN, and XOAUTH2. Password-based `smtplib.login()` is followed by `SMTPServerDisconnected` with no SMTP reply code. Host, port, and sender match the Gmail settings; the connected Gmail MCP profile resolves to the same account. No message was accepted. This narrows the issue to the local SMTP authentication path but does not reveal Google's exact rejection reason.
- **Next action:** Prefer Gmail OAuth2/XOAUTH2 or Gmail API for the project. An app password is an alternative only if the account is eligible; SMTP does not trigger an interactive 2-Step Verification prompt. Use a new delivery ID for any later send attempt.
