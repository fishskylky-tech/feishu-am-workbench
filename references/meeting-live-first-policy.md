# Meeting Live-First Policy

Use this file whenever the input is a meeting note, transcript, post-meeting summary, or meeting review.

## Default policy

Meeting scenarios are high-context tasks.

The default behavior is:

1. attempt gateway Stage 1: resource source resolution
2. attempt gateway Stage 2: customer resolution from live `客户主数据`
3. attempt gateway Stage 3: minimum targeted reads needed for this meeting
4. only then continue to meeting analysis, meeting type classification, and write planning

Do not default to single-file analysis when live Feishu context is available.

## Execution gate

Before doing formal meeting analysis, execute this gate in order:

1. identify candidate customer names from the meeting input
2. attempt gateway Stage 1
3. attempt gateway Stage 2
4. if customer resolution succeeds, attempt the minimum Stage 3 reads needed for this meeting
5. only after the gate result is known, continue to:
   - context recovery conclusion
   - meeting type classification
   - write ceiling decision
   - write candidate planning

Do not output a formal meeting conclusion before the gate result is known.

For Stage 1, do not stop at environment inspection.
The scenario must first check the repository runtime source layer before concluding that live lookup cannot proceed.

## Allowed fallback conditions

Single-file fallback is allowed only when at least one of these is true:

- live resource access is unavailable
- permission or scope is insufficient
- the customer cannot be resolved with enough confidence
- the relevant live context truly does not exist
- the user explicitly accepts a local-only fallback

The following is not, by itself, a valid fallback reason:

- no obvious environment variable or direct config was seen at first glance

## Status semantics

- `not-run`
  - the gateway was not executed
- `context-limited`
  - the gateway was executed, but the live results were incomplete
- `completed`
  - the needed live context was recovered
- `partial`
  - the gateway recovered enough context to proceed, but some expected sources were still missing

Do not use `context-limited` when the scenario never attempted the gateway.

## Minimum meeting diagnostics

When the meeting scenario attempts live recovery, show at least:

- whether live resource resolution was attempted
- whether customer resolution succeeded
- which live sources were actually read
- which expected sources were missing
- why fallback happened if fallback was used

## Forbidden shortcuts

Do not do these in a meeting scenario unless fallback conditions are met:

- start with single-file analysis and treat it as the default path
- output `not-run` without stating why the gate was not executed
- claim that live workbench config is unavailable before checking the repository runtime source layer
- describe live customer records as missing when no live query was attempted
- classify the meeting as a fully grounded customer thread before customer resolution ran
