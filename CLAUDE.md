# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A local CLI that collects semiconductor / automation-equipment industry news from GDELT and MSIT (Korean Ministry of Science and ICT) press-release RSS, normalizes and deduplicates it, and optionally emails a preview via SMTP. It is an MVP: no scheduling, no AI summarization, no shared/operational database, and no production email delivery yet. See `README.md` for the full source table and data-flow diagram, and `project_memories/` (`STATE.md`, `OPEN_ISSUES.md`, `DECISIONS.md`, `ARCHITECTURE.md`, `INCIDENTS.md`, `REPOSITORY_MAP.md`) for current status, open questions, and the rationale behind past decisions — read `STATE.md` and `OPEN_ISSUES.md` before starting new work, and update the relevant memory file when you make a decision or finish a task.

## Commands

Requires Python 3.12+. No third-party runtime dependencies (standard library only); `pytest` is required to run tests.

```bash
# Live collection from GDELT + MSIT RSS, text preview
python -m briefing --query '(Infineon OR ASE OR HYUNDAI OR MOBIS)' --hours 24 --limit 25

# Offline collection from a fixture (no network), with email preview validation
python -m briefing --input tests/fixtures/articles.json --email-check

# Normalized output as JSON instead of text
python -m briefing --query 'semiconductor OR automation' --json

# Actually send mail (requires SMTP_* env vars from .env, --to, and a stable --delivery-id)
python -m briefing --query '...' --send --to someone@example.com --delivery-id 2026-11-25-am

# Run the full test suite
python -m pytest -q

# Run a single test file / test
python -m pytest tests/test_briefing.py -q
python -m pytest tests/test_briefing.py::ClassName::test_name -q
```

SMTP credentials go in a local `.env` (see `.env.example`); never commit `.env` or paste credentials into chat. `tests/test_sources.py` currently expects a removed `collect_sources(query, hours, limit, deepsearch_key)` signature (DeepSearch was removed) and is known to fail — see `project_memories/STATE.md` / `REPOSITORY_MAP.md` before changing `collect_sources`.

## Architecture

Everything runs through `briefing/__main__.py`'s `main()`, driven by argparse with a mutually exclusive `--query` (live) vs `--input` (offline fixture) source.

1. **Collection** (`briefing/__main__.py`): `collect()` calls the GDELT DOC API (JSON, no key); `collect_msit_rss()` parses the MSIT RSS feed (stdlib `xml.etree`, no key). `collect_sources()` runs both independently and merges them — **a failure in one source does not drop the other's results**; each source's ok/failed status is carried through to the CLI output in `result["sources"]`, and a failure must never be silently hidden.
2. **Normalization**: GDELT rows go through `normalize()`, RSS rows are normalized inline in `collect_msit_rss()`. Both validate the URL (http/https, has a hostname, no embedded control characters or credentials) and require a non-empty title before accepting a record; invalid rows are counted in `rejected`, not dropped silently.
3. **Deduplication**: `collect_sources()` merges GDELT + MSIT RSS batches and drops exact duplicate URLs (GDELT checked first, so an MSIT RSS duplicate of a GDELT item is dropped).
4. **Rights boundaries are load-bearing, not incidental** — do not relax them without checking `project_memories/OPEN_ISSUES.md` (ISSUE-001, ISSUE-002) first:
   - GDELT is discovery metadata only (title/link/observed timestamp) — GDELT's dataset license does not grant rights to the linked publisher's article text, and the code never fetches or stores article bodies from GDELT links.
   - MSIT RSS item descriptions are only surfaced as a `summary` when the feed item itself carries an explicit 공공누리 제1유형 / KOGL Type 1 rights marker (checked via regex on the item's `rights`/`dc:rights` field); otherwise only title + link go out.
   - GDELT's `seendate` is an observation timestamp, not the original publication time, and is rendered as such (`observed_at`, not `published_at`).
5. **Output**: `render()` produces the human-readable text preview used both for stdout and as the email body; `--json` dumps the normalized `result` dict instead.
6. **Email** (`briefing/email.py` + `briefing/delivery.py`): `build_message()`/`validate_message()` build and sanity-check an `EmailMessage` (subject, recipient, plaintext body, valid article links) without sending. Actual sending (`--send`) additionally requires a non-partial/non-empty `result["status"]` (see the `status` gate in `main()` — `invalid_records`/`partial`/`empty` block sending), all four `SMTP_*` env vars, `--to`, and `--delivery-id`. `DeliveryLedger` (SQLite) makes delivery idempotent per `--delivery-id`: `claim()` atomically reserves the key, `dispatch()` sends and records `sent`/`failed`/`unknown` — an unclear SMTP outcome is recorded as `unknown` and is never auto-retried, by design (see `project_memories/DECISIONS.md` / `OPEN_ISSUES.md` ISSUE-009 for the current unresolved Gmail SMTP auth issue).

## Query syntax

CLI queries use an `(A OR B OR C)`-style string. For GDELT it's passed straight through as the API's `query` param. For MSIT RSS, `collect_msit_rss()` parses the same string by splitting on `OR` (case-insensitive) and keeps an item only if its title (or its description, when licensed) contains at least one term — it does not understand `AND`/`NOT` or nested boolean logic.
