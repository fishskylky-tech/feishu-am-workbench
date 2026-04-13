# Loading Strategy

This document explains the progressive disclosure loading strategy for the `feishu-am-workbench` skill.

## Overview

The skill follows a three-tier progressive disclosure model based on Google ADK standards:

- **L1 (Metadata)**: ~150 tokens - Always loaded
- **L2 (Core Instructions)**: ~2,000 tokens - Loaded when skill activates
- **L3 (Extended References)**: ~17,327 tokens total - Loaded on-demand

This design minimizes agent context window usage while preserving full functionality.

## L1: Metadata (~150 tokens)

Always loaded by the agent platform.

**Contents**:
- `name`: feishu-am-workbench
- `description`: Skill trigger conditions and use cases
- `compatibility`: Runtime prerequisites
- `tags`: Categorization and discovery
- `version`: Skill version

**Location**: Frontmatter in `SKILL.md`

## L2: Core Instructions (~2,000 tokens)

Loaded when the skill is activated by the agent.

**Contents**:
- Runtime Prerequisites
- Use This Skill When
- Core Workflow (simplified)
- Hard Rules (checklist only)
- Extraction First
- Output Pattern (template only)
- Write Order
- Closed Loop
- Scope

**Location**: Main body of `SKILL.md` (excluding detailed reference links)

## L3: Extended References (~17,327 tokens)

Reference documents in `references/` loaded on-demand based on task context.

### Loading Tiers

#### L3-Always-Load-First (if accessing Feishu)

**Total**: ~1,004 tokens

| Document | Tokens | When to Load |
|----------|--------|--------------|
| feishu-workbench-gateway.md | 1004 | Whenever task accesses Feishu workbench resources |

#### L3-Scenario: Meeting Tasks

**Total**: ~3,600 tokens

| Document | Tokens | When to Load |
|----------|--------|--------------|
| meeting-context-recovery.md | 855 | Meeting note, transcript, post-meeting task |
| meeting-live-first-policy.md | 619 | Meeting-related task before analysis |
| meeting-type-classification.md | 591 | After context recovery, before routing |
| meeting-output-standard.md | 517 | Finalizing meeting output |
| meeting-note-doc-standard.md | 332 | Creating meeting-note cold-memory doc |

#### L3-Scenario: Write Operations

**Total**: ~4,647 tokens

| Document | Tokens | When to Load |
|----------|--------|--------------|
| update-routing.md | 1510 | Write planning and routing decisions |
| actual-field-mapping.md | 1385 | Base write with specific field names |
| schema-compatibility.md | 896 | Schema drift detected |
| live-schema-preflight.md | 856 | Before any Base or Todo write |

#### L3-Scenario: Customer Operations

**Total**: ~1,307 tokens

| Document | Tokens | When to Load |
|----------|--------|--------------|
| master-data-guardrails.md | 706 | Changing customer master data |
| customer-archive-rules.md | 601 | Touching customer archive doc |

#### L3-Scenario: Extraction Tasks

**Total**: ~849 tokens

| Document | Tokens | When to Load |
|----------|--------|--------------|
| entity-extraction-schema.md | 615 | Parsing any mixed input |
| fact-grading.md | 234 | After extraction, before change plan |

#### L3-Scenario: Common Patterns

**Total**: ~1,344 tokens

| Document | Tokens | When to Load |
|----------|--------|--------------|
| task-patterns.md | 1344 | Executing well-known task types |

#### L3-On-Demand

**Total**: ~3,576 tokens

| Document | Tokens | When to Load |
|----------|--------|--------------|
| base-integration-model.md | 820 | Extending Base table access |
| workbench-information-architecture.md | 770 | Interpreting workbench layer relationships |
| minimal-stable-core.md | 672 | Evaluating backward compatibility |
| feishu-runtime-sources.md | 571 | Runtime resource discovery |
| money-and-contract-rules.md | 375 | Contract or money inputs |
| live-resource-links.example.md | 73 | Runtime setup examples |

## Loading Metadata

Each reference document includes YAML frontmatter with loading metadata:

```yaml
---
title: Document Title
load_triggers:
  - user_input_contains: [keyword1, keyword2]
  - task_type: [type1, type2]
  - skill_stage: [stage1, stage2]
  - condition: specific loading condition
load_priority: critical | high | medium | low
estimated_tokens: 500
dependencies: [doc1, doc2]
tier: L3-always | L3-scenario-* | L3-on-demand
---
```

### Metadata Fields

- **title**: Document title
- **load_triggers**: Conditions that trigger loading
  - `user_input_contains`: Keywords in user input
  - `task_type`: Task type match
  - `skill_stage`: Skill execution stage
  - `condition`: Other trigger conditions
- **load_priority**: Loading priority (critical, high, medium, low)
- **estimated_tokens**: Token count estimate
- **dependencies**: Other documents this one depends on
- **tier**: Loading tier classification

## Token Budget Analysis

### Maximum Load (All References)

- L1: ~150 tokens
- L2: ~2,000 tokens
- L3: ~17,327 tokens
- **Total**: ~19,477 tokens

### Typical Scenario Loads

#### Meeting Scenario
- L1: 150
- L2: 2,000
- Gateway: 1,004
- Meeting refs: 3,600
- **Total**: ~6,754 tokens (35% of max)

#### Write Scenario
- L1: 150
- L2: 2,000
- Gateway: 1,004
- Write refs: 4,647
- **Total**: ~7,801 tokens (40% of max)

#### Customer Update
- L1: 150
- L2: 2,000
- Gateway: 1,004
- Customer refs: 1,307
- Extraction refs: 849
- **Total**: ~5,310 tokens (27% of max)

## Implementation Strategy

### Current Phase: Documentation-Based

The current implementation relies on:

1. **Documentation conventions**: Clear "when to load" guidance in SKILL.md
2. **Frontmatter metadata**: Machine-readable loading hints in each reference
3. **Agent discipline**: Agents follow loading guidance

This approach works on all agent platforms immediately, though it depends on agent behavior.

### Future Enhancements

#### Phase 1: Technical Loader (Optional)
- Read frontmatter metadata
- Programmatically determine which references to load
- Provide loading recommendations to agent

#### Phase 2: Platform Integration (Optional)
- Support native progressive loading APIs when available
- Integrate with platform-specific resource loading mechanisms

#### Phase 3: Monitoring & Optimization (Optional)
- Track actual token usage by scenario
- Monitor context window utilization
- Warn when approaching limits
- Dynamically optimize loading strategy based on usage patterns

## Verification

To verify the progressive disclosure implementation:

1. **Check frontmatter**: All 21 reference files have loading metadata
2. **Check SKILL.md**: Includes "Skill Loading Tiers" section with L1/L2/L3 breakdown
3. **Check INDEX.md**: Includes loading strategy table with priorities and token estimates
4. **Check ARCHITECTURE.md**: Includes progressive disclosure design section
5. **Token budget**: Total L3 budget is reasonable (~17K tokens, loads 27-40% in typical scenarios)

## Benefits

1. **Reduced context window usage**: Only load what's needed for the current task
2. **Faster agent startup**: Core instructions are compact and focused
3. **Better scalability**: Can add more references without bloating base skill
4. **Platform compatibility**: Works on platforms without native progressive loading
5. **Future-ready**: Metadata enables technical loaders when needed

## Trade-offs

1. **Agent discipline**: Current approach relies on agents respecting loading guidance
2. **No hard enforcement**: Documentation-based approach has no technical enforcement
3. **Manual maintenance**: Token estimates need periodic updates
4. **Complexity**: More structure to maintain vs. flat documentation

## Maintenance

### When adding new references:

1. Add frontmatter with loading metadata
2. Update `references/INDEX.md` loading strategy table
3. Update `SKILL.md` appropriate loading tier section
4. Update `ARCHITECTURE.md` progressive disclosure section if tier totals change
5. Recalculate token budget and verify typical scenario loads

### When updating references:

1. Update `estimated_tokens` in frontmatter if content significantly changes
2. Update INDEX.md token estimate
3. Recalculate tier totals if needed

### Periodic review:

- Quarterly: Verify token estimates match actual counts
- After major changes: Validate typical scenario loads stay reasonable
- Before releases: Ensure all references have frontmatter metadata
