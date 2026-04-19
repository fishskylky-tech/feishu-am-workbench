# SECURITY-MODEL.md

**Last Updated:** 2026-04-19

---

## Overview

This document describes the security model for the Feishu AM Workbench skill. The primary security concern is protecting sensitive customer data and Feishu access credentials.

## Security Principles

### 1. Credentials Never Committed

- Feishu tokens, API keys, and access credentials **must not** be committed to the repository.
- All credential configurations **must** use environment variables or local config files excluded from version control.

### 2. Customer Data Protection

- Customer names appearing in file names are considered sensitive and should be sanitized.
- Real customer data in transcripts and meeting notes should never be committed without sanitization.
- The `archive/` directory contains customer-sensitive materials and is excluded from version control.

### 3. Write Confirmation Gate

- All Feishu write operations require explicit user confirmation before execution.
- The skill operates in **recommendation mode** by default, presenting proposed changes for review.
- Writes are only executed after user approval.

## Files Excluded from Version Control

| Pattern | Reason |
|---------|--------|
| `.env` | Contains Feishu tokens and API keys |
| `.env.local` | Local environment overrides |
| `.secrets.baseline` | Contains known secret signatures |
| `archive/` | Customer-sensitive meeting transcripts and materials |
| `tests/fixtures/transcripts/*.txt` | Real customer/project names in filenames |
| `.planning/` | Internal milestone notes and user context |
| `docs/assessment-checklist.md` | Internal evaluation documents |
| `docs/loading-strategy.md` | Internal loading strategy |

## Runtime Security

### Feishu Token Handling

- Tokens are sourced from environment variables at runtime
- The skill uses `lark-cli` for authenticated Feishu API calls
- Token refresh is handled by `lark-cli`, not by the skill directly

### Schema Validation Before Writes

Before any write operation:
1. Confirm target table exists in live Feishu Base
2. Confirm target field exists
3. Confirm field type matches intended write
4. For `select`/`multi_select` fields, fetch live options and resolve against those

### Idempotency Protection

- Duplicate writes are prevented via idempotency checks
- Update routing rules ensure the same logical update is not applied multiple times

## Secrets Detection

The repository uses `detect-secrets` baseline file (`.secrets.baseline`) to prevent accidental secret commits. The baseline is regularly updated when new secret types are introduced.

## Security Best Practices for Contributors

1. **Never commit credentials** — Use `.env` files excluded from git
2. **Sanitize filenames** — Remove real customer names from file paths
3. **Review before commits** — Run `git diff` and check for sensitive content
4. **Update secrets baseline** — When adding new credential patterns, update `.secrets.baseline`

## Vulnerability Reporting

If you discover a security vulnerability in this skill, please report it via GitHub Issues with the label `security`. Do not disclose security issues publicly before they are addressed.

---

*This security model follows the principle of "local-first, safe-write" — keeping sensitive data local while ensuring all remote writes are intentional and confirmed.*
