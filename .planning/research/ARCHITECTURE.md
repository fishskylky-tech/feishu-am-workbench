# Research: Architecture

## Core Direction

The safest v1.1 path is to extract a canonical scene runtime contract from the existing meeting write-loop path, then expand scene by scene. The project already has the right foundation; what is missing is an explicit runtime layer for scene orchestration.

## Stable Foundation

- runtime/gateway.py remains the live access and safety boundary
- runtime/live_adapter.py remains the thin targeted-read layer
- runtime/schema_preflight.py and runtime/write_guard.py remain non-bypassable write gates
- runtime/todo_writer.py remains the concrete writer implementation for current safe writes

## New Orchestration Layer

- Add a scene runtime module for scene input, execution, and result contracts
- Add a scene registry/router that maps scene names to implementations
- Keep rendering separate from scene logic so structured results stay stable

## Build Order

1. Define minimal scene runtime contracts and routing.
2. Convert meeting-write-loop into the canonical post-meeting scene runtime.
3. Add customer-recent-status as the second validating scene.
4. Extract shared renderer and scene registry once two scenes exist.
5. Add archive-refresh and then todo-capture-update.

## Architectural Risks

- Reusing eval bridge logic as production architecture without extracting contracts
- Letting gateway grow back into a full business-context assembler
- Creating a second write path beside the existing guarded path
- Regressing from workflow-driven scenes to table-driven modules
- Letting semantic contracts bloat to mirror live schema
