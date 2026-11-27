# Open Issues

## ISSUE-001 — RSS item rights and summaries

- **Status:** Open
- **Question:** Can the selected feed's descriptions be used in the internal email, and how is each item's KOGL Type 1 marking represented?
- **Current guard:** The local MVP omits all RSS descriptions, including items with rights markers. Description reuse is a future scope decision.
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
- **Impact:** Empty results are blocked. Partial collection can be sent with a warning when another source supplies valid articles; GDELT recovery is not a prerequisite for that limited result.
- **Next action:** Retry a live sample later at a lower request frequency and inspect GDELT response guidance if 429 persists.

## ISSUE-011 — Cloud database integration pending

- **Status:** Open (2026-11-27). User chose Supabase Free and deferred connection configuration.
- **Impact:** Schema/store/ledger code is prepared, but real migration, TLS, role grants, rollback and concurrent claims are unverified. No scheduled cloud sending.
- **Next action:** Follow `docs/database-setup.md` with an isolated Supabase database. Run the five integration checks and runtime permission checks, then migrate SQLite history and verify backup/restore. Fixed-window scheduling and claim/replay are implemented; real database verification remains pending.

## ISSUE-012 — Hosted scheduler verification pending

- **Status:** Open (2026-11-27).
- **Finding:** GitHub Actions dry-run workflow passes local actionlint. It has not been run on GitHub; scheduled jobs remain opt-in.
- **Impact:** Local tests do not establish runner timing or detect entirely missing cron events. Workflow creation time only estimates the intended slot within a six-hour bound.
- **Next action:** Run workflow_dispatch after publishing, inspect artifacts and timing, then enable dry-run scheduling and assess missed-run monitoring. Keep production sending disabled until database/history and operational checks pass.
