# Planned Architecture

The project is in planning; this describes the agreed target flow, not implemented components.

## Components and Data Flow

1. A morning scheduled run starts collection for the overnight window (exact schedule TBD).
2. Independent GDELT and NAVER API HUB clients retrieve global and Korean news.
3. Provider responses are normalized to a shared article record: title, publisher, publication time, permitted snippet or text, and original URL.
4. Deterministic processing applies the KST time window, deduplicates records, and filters for industry relevance. Query keywords require user input before implementation.
5. GPT classifies and summarizes selected records using only supplied, permitted source material.
6. A Korean digest includes per-item source links and, after a provider is selected, dated FX and index values.
7. The digest is delivered to a team channel (TBD); run status, source failures, and delivery outcomes are recorded.

## Boundaries and Reliability

- Keep source clients independent and isolate provider-specific parsing from the shared article format.
- Keep time-window checks, deduplication, and output validation deterministic; GPT is not the authority for source facts.
- Set request timeouts and retry transient failures only. Distinguish source outages from empty results, and continue processing other sources when one fails.
- Preserve source links; provide a deterministic fallback if model output is unavailable or invalid.
- Test with saved response fixtures and mocked clients; CI must not depend on live APIs.
- Keep credentials in environment variables or repository secrets. Begin scheduled delivery in dry-run mode and prevent overlapping runs before production sends.
- Check provider terms before storing content, sending it to GPT, or distributing summaries internally.
- Store explicit time zones; label market values with source and as-of time.

## LLM Approach

Recursive Language Models (RLM) are not needed initially. API queries, deterministic filtering, deduplication, and bounded batches should keep daily inputs manageable. Reconsider only if measured volume or evaluation demonstrates a context-length or cross-document synthesis limitation.
