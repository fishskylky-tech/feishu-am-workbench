# Codebase Map: Stack

## Summary

This repository is a documentation-first skill project with a thin Python runtime for live Feishu access, a unittest-based validation layer, and GitHub/GSD planning artifacts for ongoing evolution.

## Primary Technologies

| Area | Current stack | Notes |
|------|---------------|-------|
| Skill packaging | Markdown-first skill repository | Root docs, SKILL.md, references/, WORKFLOW.md, ROADMAP.md |
| Runtime | Python 3.10+ | Local execution only; repo includes runtime package and entrypoints |
| Live integration | lark-cli | User-authorized Feishu Base / Drive / Task access through CLI wrappers |
| Testing | Python unittest | tests/ plus eval runner and fixture-driven checks |
| Evaluation | Structured eval assets | evals/evals.json + evals/runner.py + meeting_output_bridge.py |
| Planning | GSD `.planning/` artifacts | Brownfield initialization added in this run |
| Source control | Git + GitHub private repo | Issues, PRs, Discussions, Projects already active |

## Runtime Dependencies

- Python stdlib-heavy implementation in runtime/
- Local `.env` and `FEISHU_AM_*` environment variables
- `lark-cli` with valid user auth and scopes for `base`, `drive`, and `task`
- Feishu resources wired through runtime source loader instead of committed secrets

## Operational Model

- Repository rules and references define the operating model.
- Python runtime handles resource discovery, live probing, schema preflight, and guard rails.
- Scene-level logic currently centers on meeting analysis and Todo write execution.
- Validation is based on real-case transcripts plus regression tests.

## Strengths

- Clear split between prompt/rules and executable runtime.
- Live-first design is documented and partially enforced in code.
- Testing is already aimed at realistic customer scenarios instead of toy examples.

## Current Limitations

- No package manifest; environment setup is mostly convention-based.
- Runtime depends on local Feishu scopes and personal resource wiring.
- Expanded tables are modeled, but only part of the read/write surface is live in production paths.