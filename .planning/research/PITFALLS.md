# Research: Pitfalls

## Pitfall 1: Overgeneralizing too early

- Warning signs: roadmap work shifts from personal AM value to abstract portability before core loops are stable
- Prevention: treat personal daily value as the main acceptance bar for v1
- Best phase to address: Phase 1 and Phase 6

## Pitfall 2: Treating live schema as prompt context

- Warning signs: more hardcoded field names, larger prompt load, more fragile updates
- Prevention: keep semantic contracts minimal and rely on live discovery for the rest
- Best phase to address: Phase 2 and Phase 5

## Pitfall 3: Letting scenes bypass runtime guard rails

- Warning signs: direct Feishu writes from scene code, hidden fallback behavior, synthetic context claims
- Prevention: keep gateway, preflight, guard, and writer boundaries explicit
- Best phase to address: Phase 3 and Phase 4

## Pitfall 4: Confusing archive structure with trustworthy canonical truth

- Warning signs: duplicate customer docs, stale links, meeting-note routing based only on filename
- Prevention: strengthen archive canonicalization and link maintenance before deeper archive automation
- Best phase to address: Phase 3 and Phase 5

## Pitfall 5: Measuring output quality only by prose quality

- Warning signs: impressive summaries with weak traceability, no regression protection, or hidden live failures
- Prevention: keep transcript-based evals and structured assertions as release gates
- Best phase to address: Phase 4 and Phase 6