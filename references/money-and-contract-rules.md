# Money And Contract Rules

Money fields are high risk. Treat them with stricter source rules.

## Separate these amount types

- `theoretical_value`
  - A modeled, forecast, or conditional upside number
- `contract_value`
  - Signed commercial amount
- `paid_value`
  - Actually collected amount
- `unpaid_value`
  - Outstanding collection
- `draft_value`
  - Proposal or internal estimate not yet signed

Do not merge them into one number.

## Source priority

Highest to lowest:

1. User's explicit correction in the current conversation
2. Existing contract or collection record already confirmed in Feishu
3. Local contract, SOW, or settlement materials
4. Historical plan decks or internal projections
5. Model inference

Lower-priority sources cannot overwrite higher-priority sources without calling out the conflict.

## Write rules

- Never present a theoretical incentive, optional fee, or unexecuted clause as actual revenue.
- If an older document shows a large modeled total and the user clarifies the real signed amount, preserve only the real signed amount as the main fact.
- When the reason for zero revenue is known only at a high level, state that plainly instead of inventing operational detail.
- If a contract period and amount are known, store them even if the detailed line items are not.
- Historical contracts should default to the customer archive, not `合同清单`.
- Use `合同清单` only for contracts that still matter to current management, such as active validity tracking, renewal follow-up, receivable tracking, or in-flight execution.

## Archive wording

In the customer archive:

- Put actual signed and paid numbers in the main history.
- Put optional or unexecuted mechanisms in a note, not in the headline amount.
- If collections are partial, show contract amount and paid amount separately.
