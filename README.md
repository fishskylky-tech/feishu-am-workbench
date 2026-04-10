# feishu-am-workbench

Personal Codex skill for running a Feishu-based AM workbench.

This repository version-controls the skill that analyzes customer materials, Feishu Base records, customer archive docs, and Feishu Todo items for day-to-day account management.

## What this skill does

- Analyzes mixed AM inputs:
  - local customer folders
  - meeting notes
  - user notes
  - Feishu Base workbench data
  - customer archive docs
  - public customer updates
- Produces:
  - account analysis and judgment
  - proposed updates for the Feishu workbench
  - confirmed write-back into Base, docs, and Todo
- Enforces operating rules:
  - one canonical customer archive per customer
  - absolute dates only
  - customer master as protected snapshot layer
  - meeting-note cold memory in docs, not Base long text
  - semantic Todo dedupe with explicit owner
  - runtime schema compatibility checks before write-back

## Repository layout

- [SKILL.md](/Users/liaoky/Documents/工作/神策/feishu-am-workbench/SKILL.md)
  - main operating instructions for the skill
- [agents/openai.yaml](/Users/liaoky/Documents/工作/神策/feishu-am-workbench/agents/openai.yaml)
  - skill metadata for agent discovery
- [references/](/Users/liaoky/Documents/工作/神策/feishu-am-workbench/references)
  - supporting rules, field mappings, routing rules, and compatibility notes

## Current design stance

The skill does not assume the Feishu workbench schema is frozen.

It uses:

- stable business rules in the skill itself
- cached mapping files for fast reference
- live schema and live option discovery before write-back
- alias fallback only when the match is narrow and safe
- no-write fallback when schema drift makes a write unsafe

## Install locally

If this repository is the source of truth, sync it into Codex skills with either:

1. direct copy into `~/.codex/skills/feishu-am-workbench`
2. symlink from this repository to `~/.codex/skills/feishu-am-workbench`

Example symlink flow:

```bash
mv ~/.codex/skills/feishu-am-workbench ~/.codex/skills/feishu-am-workbench.bak
ln -s "/Users/liaoky/Documents/工作/神策/feishu-am-workbench" ~/.codex/skills/feishu-am-workbench
```

Only do this after confirming the repository version is the desired source of truth.

## Working model

Use GitHub PRs for meaningful skill changes:

- schema compatibility changes
- write-back rule changes
- customer archive template changes
- Todo routing changes
- Base field mapping updates

Small mapping refreshes are fine, but business-rule changes should be reviewed before merge.

## Next recommended step

Make this repository the canonical source for the installed local skill by replacing the current local skill directory with a symlink to this repo.
