# Changelog

All notable changes to `feishu-am-workbench` should be recorded here.

This project follows a lightweight changelog style:

- `Added` for new capabilities
- `Changed` for behavior updates
- `Fixed` for corrections
- `Removed` for retired behavior

## [0.1.0] - 2026-04-10

### Added

- Initial GitHub-managed repository for `feishu-am-workbench`
- Core skill workflow for Feishu AM analysis, recommendation, and confirmed write-back
- Reference rules for:
  - field mapping
  - routing and idempotency
  - fact grading
  - contract and money interpretation
  - customer archive rules
  - task patterns
  - workbench information architecture
  - schema compatibility

### Changed

- Promoted live schema discovery and live option discovery to primary write-safety mechanisms
- Treated cached mapping files as compatibility snapshots instead of permanent truth

### Fixed

- Clarified Todo rules:
  - explicit owner required
  - semantic dedupe required
  - parent/subtask structure preferred for related work
- Clarified customer archive uniqueness and meeting-note cold-memory routing
