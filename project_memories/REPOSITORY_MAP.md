# Repository Map

Last checked: 2026-11-24

- `README.md`: current GDELT + MSIT RSS source list, rights boundary, and commands.
- `briefing/__main__.py`: GDELT/RSS requests, parsing, normalization, URL deduplication, per-source status, CLI and preview.
- `briefing/email.py`: email validation and STARTTLS SMTP sender.
- `briefing/delivery.py`: SQLite delivery ledger and no-auto-retry dispatch behavior.
- `tests/test_briefing.py`: GDELT parsing, normalization, retry behavior, and message validation.
- `tests/test_sources.py`: source normalization/merge tests. Update for RSS source behavior before relying on it.
- `tests/test_delivery.py`, `tests/test_cli_send.py`: delivery-state and send-gate behavior.
- `tests/fixtures/articles.json`: offline synthetic article response.
- `docs/collection-test.md`: offline and provider test instructions.
- `docs/email-template.md`: proposed email format awaiting approval.
- `.env.example`: local configuration example; `.env` is ignored. The current sources need no API key.
- `docs/system-architecture.md`, `docs/development-plan.md`, `docs/cron-job-plan.md`: broader deployment design; verify planned state against current code.
