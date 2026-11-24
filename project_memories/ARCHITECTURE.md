# Architecture

## Implemented data flow

1. CLI accepts an explicit industry/company query, lookback hours, and per-run result limit.
2. GDELT DOC API and the Ministry of Science and ICT (MSIT) press-release RSS are requested independently. RSS is read with Python's standard-library XML parser; no API key is needed.
3. Each response is validated and normalized to title, source/publisher, provider, URL, timestamp, and language. GDELT contributes discovery metadata only. An RSS description is exposed as a summary only when the feed item itself marks KOGL Type 1; otherwise only its title and URL are retained.
4. Exact URL duplicates are removed. Per-source status is retained; one source failure does not erase the other source's results. Partial results are marked and cannot be sent by the current CLI.
5. Output is a JSON/text email preview. A local SQLite delivery ledger prevents duplicate sends and avoids automatic retries for unknown outcomes.

## Not implemented

- LLM summarization, market-data collection, CI, scheduling, managed delivery state, and production monitoring.
- Automatic fallback that hides a source failure. Current behavior is explicit partial collection.

## Boundaries

- GDELT dataset terms do not establish the linked publishers' rights to article text.
- DeepSearch has been removed from the runtime and source list.
- GDELT data attribution does not grant rights to linked publisher article text. Never fetch or send those article bodies to an LLM by default.
- MSIT RSS items require an explicit KOGL Type 1 marker before the feed description can be used. No article body is fetched.
- NAVER is deferred pending confirmation of search-result display, email delivery, AI, and retention rights.
- Keep any future API credentials in environment variables or local `.env`; do not print them.
