# Research: Stack

## Recommendation

For this project, the right stack is not a heavier application framework. It is a focused combination of:

- Markdown-based skill operating model
- Python runtime for deterministic orchestration and safety
- lark-cli as the Feishu execution adapter
- unittest + eval assets for regression proof
- GSD planning artifacts for incremental brownfield delivery

## Why This Stack Fits

### Prompt/rules layer

- The domain is highly policy-driven.
- references/ and SKILL.md already encode substantial operating knowledge.
- Replacing this with a conventional app UI would not solve the core problem.

### Python runtime layer

- Resource discovery, schema validation, write guard, and normalized write results all benefit from code rather than prompt prose.
- The existing runtime is already the right place for thin deterministic logic.

### lark-cli integration layer

- Directly matches the personal AM workflow.
- Gives access to Base, Drive, and Task without embedding private credentials into repo code.

### Planning/execution layer

- The missing piece was not more design docs; it was phase-based brownfield execution control.
- GSD fills that gap without changing the runtime architecture.

## Keep

- Python 3.10+ runtime
- lark-cli as the live adapter
- env-based private configuration
- markdown references as domain source material
- unittest + eval runner hybrid validation

## Avoid

- Full webapp rewrite before the operating model is mature
- Full field mirroring of Feishu schemas
- Auto-write behavior that bypasses runtime checks
- Platform-specific business logic that locks the skill to one agent host