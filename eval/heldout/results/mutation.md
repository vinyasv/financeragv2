# Grader mutation test (post-hoc)

Grader: `google/gemini-3.8-flash` (frozen prompt). Mutator: `anthropic/claude-sonnet-5`. Checker: `openai/gpt-5.1`.
A planted error is caught when the grader no longer marks the target claim "stated".
Valid mutations are those the checker agrees no longer state the claim.

- Targets: 555. Mutation failed (no applicable edit): 0.
- Checker rejected the mutation (claim still stated): 33.

| slice | caught, valid mutations | caught, all mutations |
|---|---|---|
| all | 100% (520/522; 95% CI 99–100%) | 98% (545/555; 95% CI 97–99%) |
| kind: text | 100% (460/461; 95% CI 99–100%) | 99% (462/465; 95% CI 98–100%) |
| kind: numeric | 98% (60/61; 95% CI 91–100%) | 92% (83/90; 95% CI 85–96%) |
| arm: v2 | 100% (202/203; 95% CI 97–100%) | 99% (213/215; 95% CI 97–100%) |
| arm: baseline_k6 | 99% (151/152; 95% CI 96–100%) | 98% (160/164; 95% CI 94–99%) |
| arm: baseline_k12 | 100% (167/167; 95% CI 98–100%) | 98% (172/176; 95% CI 94–99%) |
| error: direction | 100% (80/80; 95% CI 95–100%) | 99% (80/81; 95% CI 93–100%) |
| error: item | 99% (147/148; 95% CI 96–100%) | 99% (150/152; 95% CI 95–100%) |
| error: name | 100% (143/143; 95% CI 97–100%) | 99% (146/148; 95% CI 95–100%) |
| error: number | 100% (27/27; 95% CI 88–100%) | 100% (27/27; 95% CI 88–100%) |
| error: other | 100% (39/39; 95% CI 91–100%) | 100% (39/39; 95% CI 91–100%) |
| error: period | 99% (84/85; 95% CI 94–100%) | 95% (103/108; 95% CI 90–98%) |

## Controls

- Unmodified answer re-graded, target claim still stated: 99% (550/555; 95% CI 98–100%)
- Other stated claims wrongly failed after the mutation: 13% (166/1235; 95% CI 12–15%)

## Missed planted errors (valid mutations the grader still passed)

| arm | question | run | kind | error | claim | edit | grader quote |
|---|---|---|---|---|---|---|---|
| v2 | h052 | 2 | text | item | States that cabin electronics drove the Automotive demand | Analog Devices said demand for cabin electronics and battery management systems  → Analog Devices said demand for driver assistance systems and battery management  | cabin electronics and battery management systems drove the increase in its Automotive end market |
| baseline_k6 | h032 | 3 | numeric | period | Industrial share of total revenue % = 4,314,280 / 9,427,157: 45.76 | Using reported Industrial revenue divided by reported total revenue, the Industr → Using reported Industrial revenue divided by reported total revenue, the Industr | the Industrial end market represented **45.76%** of total revenue in fiscal 2023: $4,314,280 ÷ $9,427,157 × 100 = 45.76% |

## Manual review of the misses

- v2 h052 run 2 is an invalid mutation. The edit changed one sentence, but the answer's "Context" paragraph still says cabin electronics drove the Automotive increase, and the grader quoted it. The checker missed this. Excluding it: 520 of 521 valid planted errors caught.
- baseline_k6 h032 run 3 is a real miss. The edit relabelled a fiscal 2024 share as fiscal 2023, and the grader passed it.

## Collateral failures

After a mutation, the grader failed 166 of 1,235 other claims it had passed. 119 of those 166 were in answers where the edit changed text the grader had quoted for that claim. Counting only claims whose original quote survives verbatim in the edited answer: 47 of 670 (7%).
