# Codebase Map: Structure

## Top-Level Layout

| Path | Purpose |
|------|---------|
| README.md / ARCHITECTURE.md / STATUS.md / VALIDATION.md | Current product, architecture, status, and validation narrative |
| SKILL.md | Skill definition and runtime-facing operating rules |
| references/ | Domain rule documents loaded progressively |
| runtime/ | Python runtime for live Feishu access and safety checks |
| evals/ | Eval runner, case definitions, and meeting bridge |
| tests/ | Regression and smoke tests |
| docs/ | Supplemental technical docs such as loading strategy |
| archive/ | Historical assessment and validation material |
| external-skills/ | Vendored skill references and related tooling |

## Runtime Subsystem

- env_loader.py: loads `.env`
- runtime_sources.py: resource hint extraction
- resource_resolver.py: resource probing
- customer_resolver.py: customer matching
- gateway.py: orchestration
- schema_preflight.py: write safety validation
- write_guard.py: policy enforcement
- todo_writer.py: first normalized writer

## Validation Subsystem

- evals/evals.json: real-case definitions
- evals/runner.py: structured assertions
- evals/meeting_output_bridge.py: bridge from transcript + gateway to assertion-friendly output
- tests/: unit and regression checks for runtime, bridge, eval assets

## Documentation Pattern

- Root docs describe product intent and current state.
- references/ files define stable operating rules and scenario-specific guidance.
- CHANGELOG.md, ROADMAP.md, STATUS.md, VALIDATION.md are kept as living operational artifacts.

## Brownfield Observation

The repository is already rich in domain documentation, but it previously lacked `.planning/` artifacts that convert the existing intent into GSD-manageable execution phases.