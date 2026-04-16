# Codebase Map: Testing

## Current Testing Surface

### Automated tests

- tests/test_env_loader.py
- tests/test_eval_runner.py
- tests/test_meeting_output_bridge.py
- tests/test_runtime_smoke.py
- tests/test_validation_assets.py

### Validation assets

- evals/evals.json tracks real meeting cases and assertions.
- validation reports in archive/validation-reports/ capture observed outcomes.
- VALIDATION.md defines baseline, green, and regression protocol.

## What Is Covered Well

- Runtime env loading
- Capability report behavior
- Gateway and meeting bridge output contracts
- Todo writer result normalization and dedupe behavior
- Validation asset consistency

## What Still Needs More Coverage

- Real write-path integration beyond the first Todo surface
- Expanded table queries and future write support
- Archive doc body retrieval and relevance ranking
- More schema-drift and permission-edge live cases

## Recommended Test Strategy Going Forward

- Keep unit tests around runtime primitives.
- Add scenario tests for every new scene entrypoint.
- Preserve at least one live-ish representative transcript per major meeting type.
- Add phase-linked acceptance checks as `.planning` roadmap advances.