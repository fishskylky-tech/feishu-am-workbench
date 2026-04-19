# CHANGELOG.md

All notable changes to the `feishu-am-workbench` skill are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-04-19

### Added

- **7th registered scene: `proposal`** - Generate structured proposal/report/resource-coordination draft with five-dimension output (objective, core judgment, main narrative, resource asks, open questions)
- **Meeting type taxonomy** - Classification system for meeting types with associated write ceilings
- **Scene runtime contract** - Standardized interface for scene execution and expert role loading
- **Meeting live-first policy** - Execution gate requiring live context recovery before formal analysis
- **Context hydrator** - Multi-source context recovery from Feishu Base, Docs, and meeting notes

### Changed

- **Meeting output standard** - Updated to include meeting type, write ceiling, and context recovery status
- **Entity extraction schema** - Enhanced with meeting-specific fields and fact grading
- **Scene registry** - Expanded from 5 to 7 registered scenes

### Fixed

- Archive folder resolution now uses live resource discovery
- Customer archive link resolution handles stale links correctly
- Todo dedupe logic now considers meaning, not just exact title match

---

## [1.1.0] - 2026-04-17

### Added

- **5 registered scenes**: post-meeting-synthesis, customer-recent-status, archive-refresh, todo-capture-and-update, cohort-scan, meeting-prep
- **Progressive loading tiers** - L1/L2/L3 disclosure model to minimize context usage
- **Write confirmation gate** - All writes require explicit user confirmation before execution
- **Master data guardrails** - Protected field policy for customer master table
- **Update routing rules** - Idempotency and routing logic for Feishu writes
- **Schema compatibility layer** - Handling for schema drift and alias matching

### Changed

- Separated fact extraction from judgment to prevent inferred business judgment from being presented as objective fact
- Improved date handling to use absolute time expressions only
- Customer archive creation now requires finding existing archive before creating new one

---

## [1.0.0] - 2026-04-16

### Added

- Initial release of feishu-am-workbench skill
- Feishu Base table integration for customer master data, contracts, action plans, contact maps, and competitive records
- Feishu Docs integration for customer archive documents
- Feishu Todo integration for action item tracking
- Meeting note cold-memory document standard
- Local evaluation harness (`evals/`)
- Runtime layer for live Feishu access

---

*This changelog tracks user-facing changes only. Internal technical debt, refactoring, and process changes are documented in commit messages.*
