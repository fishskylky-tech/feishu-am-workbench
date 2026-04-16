# Research: Architecture

## Recommended Component Model

### 1. Skill rule layer

- SKILL.md and references/
- Defines operating principles, scenario rules, and loading boundaries

### 2. Runtime foundation layer

- Resource source loading
- live capability probing
- customer resolution
- targeted read backends
- schema preflight
- write guard

### 3. Scene orchestration layer

- meeting-prep
- post-meeting
- account-analysis
- archive-refresh
- future proactive reporting scenes

### 4. Writer layer

- Todo writer now
- later: broader Base/doc write surfaces when safe enough

### 5. Validation layer

- eval runner
- bridge output normalization
- scenario fixtures
- regression tests

## Data Flow

1. Input arrives from user prompt or transcript.
2. Runtime resolves resources and customer context.
3. Scene requests only the next needed reads.
4. Scene produces structured observations, judgments, and candidate writes.
5. Runtime preflights and guards candidates.
6. Confirmed writes execute through normalized writer surfaces.
7. Eval/test layer verifies expected behavior.

## Suggested Build Order

1. Brownfield operating system and codebase map
2. Runtime/resource hardening
3. Context recovery across core customer tables and archive links
4. Unified safe write surface maturation
5. Expanded account model coverage (contracts, key people, competitors)
6. Proactive account intelligence outputs