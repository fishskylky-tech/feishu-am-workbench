# Codebase Map: Architecture

## High-Level Design

The repository is organized around a deliberate split between:

1. Business rules and design docs
2. A thin runtime gateway for live Feishu access
3. Eval and regression assets for real customer scenarios

## Core Runtime Flow

1. Runtime sources load private resource hints from env/files.
2. Resource resolver probes whether Base / Drive / Task resources are truly reachable.
3. Customer resolver searches live customer master data.
4. Optional targeted reads recover the minimum context needed by a scene.
5. Schema preflight and write guard evaluate write candidates.
6. Object-specific writer executes only after confirmation.

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