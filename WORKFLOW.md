# WORKFLOW.md

**Last Updated:** 2026-04-19

---

This document describes the core workflow for using the Feishu AM Workbench skill.

## Core Workflow Overview

```
User Input → Scene Classification → Context Recovery → Entity Extraction
     ↓                                                      ↓
Recommendation Review ← Analysis & Judgment ← Structured Summary
     ↓
User Confirmation
     ↓
Feishu Write (if confirmed)
     ↓
Result Report
```

## Step-by-Step Process

### Step 1: Identify Intent and Customer

1. Parse the user's request to identify the primary intent (meeting prep, post-meeting synthesis, customer status query, etc.)
2. Extract customer name(s) from the input
3. Resolve `客户ID` from `客户主数据` as the source of truth

### Step 2: Scene Selection

The skill routes the request to one of 7 registered scenes:

| Scene | Purpose |
|-------|---------|
| `post-meeting-synthesis` | Transform meeting transcripts into structured judgments |
| `customer-recent-status` | Query recent customer status across four lenses |
| `archive-refresh` | Propose archive updates from multiple sources |
| `todo-capture-and-update` | Classify and create Todo follow-ons |
| `cohort-scan` | Query aggregated customer class analysis |
| `meeting-prep` | Generate recommendation-first meeting brief |
| `proposal` | Generate structured proposal/report draft |

### Step 3: Context Recovery (Live-First Gate)

When the task involves meeting notes or transcripts:

1. **Attempt live-first**: Try to recover context from Feishu records (Base tables, docs, meeting notes)
2. **If live lookup succeeds**: Use recovered context to enrich the analysis
3. **If live lookup fails**: Fall back to local file analysis only

This gate ensures the skill always starts with the most current customer context available.

### Step 4: Entity Extraction

Extract structured information before planning any updates:

- Customer identity
- Contacts and org changes
- Competitors
- Contracts, amounts, and collections
- Risks and opportunities
- Key progress, blockers, and Todos
- Schedules and milestone dates
- Public updates and account judgment

### Step 5: Meeting Type Classification

For meeting-related tasks, classify the meeting type to determine the write ceiling:

- **Strategic**: Full archive update, all tables writable
- **Tactical**: Selected tables, focused update
- **Operational**: Minimal write, context-only

### Step 6: Produce Analysis and Recommendations

Generate two outputs:

1. **Account Analysis**: Structured summary with facts, judgment, risks, opportunities
2. **Change Plan**: Structured list of proposed updates with create vs. update decisions

### Step 7: User Confirmation

Present the recommendations to the user and wait for explicit confirmation before any Feishu write.

### Step 8: Execute Write (if confirmed)

Write order:
1. Structured Feishu tables first
2. Customer archive docs
3. Meeting-note cold-memory docs
4. Feishu Todo items last

### Step 9: Report Results

Report success, partial failure, schema drift, or blocked status clearly.

## Write Confirmation Flow

```
[Analysis Complete]
       ↓
[Show: Customer | Context Recovery | Extracted Entities | Change Plan]
       ↓
[User: "Yes, proceed" / "Modify X" / "Cancel"]
       ↓
[If confirmed]: Execute writes in order → Report results
[If modified]: Regenerate change plan → Re-confirm
[If cancelled]: Stop, no writes made
```

## Scene-Specific Workflows

### Post-Meeting Synthesis

1. Run live-first gate
2. Classify meeting type
3. Extract entities (contacts, risks, opportunities, todos)
4. Generate structured summary
5. Propose archive and action plan updates
6. Wait for confirmation
7. Write tables → Archive docs → Todos

### Meeting Prep

1. Query customer recent status
2. Generate seven-dimension brief:
   - Current status
   - Key people
   - Objectives
   - Risks
   - Opportunities
   - Suggested questions
   - Suggested next steps
3. Present to user

### Todo Capture

1. Extract action items from meeting or materials
2. Classify by intent (risk intervention, expansion, relationship, project)
3. Check for existing similar todos (dedupe by meaning)
4. Propose new todos or update existing ones
5. Wait for confirmation
6. Create or update in Feishu Todo

## Error Handling

| Error Type | Behavior |
|-----------|----------|
| Customer ambiguous | Stop and ask for clarification |
| Schema drift | Trust live schema, surface drift in change plan |
| Live lookup unavailable | Fall back to local-only analysis |
| Write blocked | Report blocked status with reasons |
| Partial failure | Report completed writes + remaining failures |

---

*This workflow follows the principle: Read carefully first, then recommend, then act only after confirmation.*
