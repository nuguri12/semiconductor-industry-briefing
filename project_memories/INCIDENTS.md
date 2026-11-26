# Incidents

## 2026-11-26 — Live-news test unblocked by official MOTIR RSS (ISSUE-004/010)

- Symptom: GDELT failed and MSIT had no matching articles within 72h, blocking live receipt verification.
- Cause: Two-source coverage was insufficient for the sampled window; the MOTIR RSS endpoint had not been located.
- Fix: Read the official RSS form action and use its empty POST endpoint. Reuse the RSS parser and preserve independent source status and title/link-only boundary.
- Verification: Today's MOTIR semiconductor-policy article passed preview, SMTP send and Gmail full-body/link receipt verification. Same-key replay did not change the ledger or produce a second matching email. Evidence in `docs/collection-test.md`.
- Prevention: Distinguish access failure, valid empty feed and insufficient topic coverage. Inspect official feed controls before concluding no feed exists. Keep GDELT's unresolved failure tracked separately.

## 2026-11-26 — SMTP test authentication recovered (ISSUE-009)

- Symptom: The earlier test disconnected during SMTP login after successful STARTTLS; no message was accepted.
- Root cause: The exact earlier server-side rejection reason remains unknown. App-password configuration resolved the observed failure without changing the sender code.
- Fix: The user configured an app password locally; retained existing STARTTLS SMTP implementation.
- Verification: CLI fixture send exited 0 with `sent` for `smtp-app-password-test-20261126-01`. Gmail INBOX independently contained the matching 14:53 KST test message, ID `1a2166a553c83cc2`, addressed to `nuguri12@gmail.com`.
- Prevention: Keep credentials out of logs/Git. Check supported account authentication before introducing Gmail API/OAuth. Preserve delivery records and do not repeat the successful test with a new key. This verifies synthetic mail delivery, not live-news collection or scheduled operation.
