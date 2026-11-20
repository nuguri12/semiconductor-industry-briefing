# Repository Map

Last checked: 2026-11-20

## Current Layout

- `README.md` — public-facing project introduction and proposed workflow.
- [Briefing plan](../docs/cron-job-plan.md) — requirements, workflow diagram, team use cases, acceptance criteria and open policy decisions.
- [System architecture](../docs/system-architecture.md) — recommended stack, component diagram, delivery state and failure recovery.
- [Development plan](../docs/development-plan.md) — engineering workflow, implementation sequence and evidence required at each stage.
- `project_memories/` — agent-facing state, architecture, decisions, unresolved issues, and this navigation guide.
- Application code, runtime configuration, tests, and CI have not yet been added.

## Update This Map When Code Is Added

Record only stable navigation points that help future development:

- Application entry point and scheduled-job configuration.
- News and market-data provider clients and shared schemas.
- GPT prompt/output validation and digest composition.
- Delivery integrations and runtime configuration/secrets.
- Unit/integration tests and CI workflows.

Verify paths against the repository before relying on them; do not assume planned modules already exist.
