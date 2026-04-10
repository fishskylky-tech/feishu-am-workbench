# Fact Grading

Use these grades to separate reliable account facts from judgment.

## Grades

- `A`
  - Directly verifiable system fact
  - Examples: confirmed Feishu record, signed contract data, public filing
- `B`
  - Clear fact stated in local historical materials
  - Examples: project summary, SOW, archived meeting memo
- `C`
  - Fact explicitly provided by the user in the current conversation
- `D`
  - Inference, synthesis, or business judgment produced by the model

## Write behavior

- `A`, `B`, `C`
  - Can be written as factual content after confirmation
- `D`
  - Can inform strategy, risk, opportunity, and recommendation fields
  - Must not be written as objective fact without clear user approval

## Conflict rule

- If grades conflict, prefer the higher-trust source.
- A user's explicit correction in the current conversation outranks any older local material for the same fact.
- If the user explicitly corrects an older material, keep the user's correction and note the older source as outdated.
- If two high-trust sources conflict, stop and surface the discrepancy before writing.
