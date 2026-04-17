# Phase 12 Discussion Log

**Date:** 2026-04-17
**Phase:** 12 - Scene Runtime Contract And Boundary Freeze
**Status:** Discussion complete

## Summary

The discussion focused on four remaining gray areas for Phase 12:
1. how much every scene result must consistently explain
2. what the primary entry experience should feel like
3. how clearly blocked or limited execution should be explained
4. how hard the first-wave scene boundaries should be frozen

The user requested non-technical, easy-to-understand framing and selected concrete preferences for all four areas.

## Questions And Answers

### Area 1: Shared result shape
**Question:** How much should every scene result consistently explain?

**Options presented:**
- A. Minimal: scene, customer found or not, enough context or not, can write or not, and the top-level blocker
- B. Standard: A plus used sources, fact vs judgment, open questions, next-step recommendations, and whether the result is recommendation-only
- C. Very light: mostly conclusion and write status, with details left to each scene

**User selection:** B

**Captured decision:** The shared scene result should use the standard level of detail so later scenes feel consistent, auditable, and understandable to business users.

### Area 2: Scene entry experience
**Question:** How should users "call" scenes in the long run?

**Options presented:**
- A. Stable scene names as the main model
- B. Keep action-specific operator commands as the main model
- C. Treat both equally as permanent first-class entry models

**User selection:** A

**Captured decision:** Stable scene names should become the primary entry model. Existing operator commands may remain temporarily for compatibility but should not define the future contract.

### Area 3: Blocked or limited execution explanation
**Question:** How clearly should the system explain why it cannot fully proceed or cannot write?

**Options presented:**
- A. Business-readable explanation only
- B. Business-readable explanation plus one deeper layer of reason
- C. Maximum available detail

**User selection:** B

**Captured decision:** Results should explain the business meaning first, then add one more layer that distinguishes missing context, customer ambiguity, permission issues, live validation failure, and safety/risk blocking.

### Area 4: Boundary freeze strength
**Question:** How hard should Phase 12 lock the first-wave boundaries?

**Options presented:**
- A. Only lock the scene list and the non-bypass safety red line
- B. Medium-strength freeze: also lock priority grouping, workflow-first split rule, and keep deferred scenes out of the first wave
- C. Maximum freeze on nearly all later implementation details

**User selection:** B

**Captured decision:** Phase 12 should use a medium-strength boundary freeze that prevents drift without over-specifying all later implementation details.

## Carry-Forward Constraints Reused

The discussion explicitly carried forward previously locked decisions instead of reopening them:
- root entry remains thin
- scenes are workflow-shaped, not table-shaped
- first-wave scene list and priority groups remain locked
- gateway, schema preflight, write guard, and writer are non-bypassable
- admin/bootstrap stays out of daily scene execution
- the existing meeting write-loop is promoted rather than replaced by a new write path

## Outcome

These decisions are formalized in `12-CONTEXT.md` and should be treated as locked inputs for any replanning of Phase 12.
