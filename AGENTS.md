<!-- GSD:project-start source:PROJECT.md -->
## Project

**Feishu AM Workbench**

Feishu AM Workbench is a personal AM skill project for Hermes/OpenClaw/Codex-style agents. It helps a Sensors Data AM use Feishu Base, Drive docs, and Task as a customer operating platform: recover live context, interpret customer materials, propose safe updates, and gradually evolve toward a reusable account-management operating model.

This is a brownfield project: the repository already has a working runtime, validation assets, a private GitHub collaboration surface, and a live Feishu workspace with customer master, contracts, actions, key people, competitors, archives, meeting notes, and a task module.

**Core Value:** Use one live-first, safety-first skill to turn AM inputs into actionable customer operating context and guarded write plans inside the existing Feishu workbench.

### Constraints

- **Tech stack**: Python runtime + lark-cli + markdown skill docs — this is already the established execution surface
- **Security**: secrets and live resource identifiers stay in env/private runtime sources — required to avoid leaking personal customer workspace data
- **Safety**: writes must remain recommendation-first and guarded — high-risk master-data updates cannot become automatic
- **Brownfield**: roadmap must respect existing runtime, docs, tests, and live workspace structures — this is not a greenfield rewrite
- **Portability**: business logic should stay portable across agent hosts — the project is intended for Hermes/OpenClaw-style usage, not one locked host
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Summary
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
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

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
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## High-Level Design
## Core Runtime Flow
## Important Modules
### runtime/gateway.py
- Main orchestration entrypoint for live runs.
- Composes resource resolution, customer resolution, schema preflight, and write guard.
### runtime/live_adapter.py
- Adapts lark-cli into runtime-friendly backends.
- Confirms Base, folder, and tasklist resources.
- Supports customer search and capability reporting.
### runtime/semantic_registry.py
- Defines table profiles and semantic slots.
- Keeps prompt/runtime semantics intentionally smaller than live schema.
- Core integrated tables today are 客户主数据, 客户联系记录, 行动计划.
### evals/meeting_output_bridge.py
- Bridges meeting transcripts, gateway output, recovered context, and Todo candidates.
- Central to current live-first validation flow.
## Architectural Style
- Docs-first domain modeling
- Thin adapters over external systems
- Recommendation-first mutation path
- Brownfield evolution with explicit roadmaps and validation assets
## Current Architectural Constraints
- Foundation layer should not auto-assemble full business context.
- Scene layer decides what to read and what to propose writing.
- Schema discovery is live, but semantic contracts remain minimal.
- Expanded business tables are modeled before they are promoted into full write paths.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.github/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
