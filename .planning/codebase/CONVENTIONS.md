# Codebase Map: Conventions

## Product and Domain Conventions

- Chinese-first business terminology for AM workflows.
- Live-first for meeting and Feishu-dependent tasks.
- Recommendation-first for writes; explicit confirmation before mutation.
- Facts, judgment, and action proposals are expected to remain separate.

## Technical Conventions

- Private resource identifiers stay out of git.
- `.env` supplements shell env; explicit env wins.
- Semantic contracts stay intentionally smaller than full live schema.
- New Base tables are added as table profiles before they are made writable.

## Documentation Conventions

- Root docs are not marketing docs; they act as execution guidance.
- STATUS.md records the actual implemented state.
- VALIDATION.md defines how truth is checked, not just what should happen.
- CHANGELOG.md is actively maintained and aligned with VERSION/evals.

## Testing Conventions

- Use real-case customer transcripts where feasible.
- Prefer regression coverage for previously observed drift/fallback mistakes.
- Validate live-first behavior explicitly, not just final text output.

## Workflow Conventions

- Personal-value-first before generalization.
- Thin runtime foundation, thicker scenario/business reasoning above it.
- Expand safely: schema preflight, protected fields, owner rules, dedupe.