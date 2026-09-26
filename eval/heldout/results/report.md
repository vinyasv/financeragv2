## Hypothesis tests (unit: question; per-question mean over runs)

| test | questions | v2 | comparator | difference [95% bootstrap CI] | wins/losses | p (sign test) | p (Holm) |
|---|---|---|---|---|---|---|---|
| H1 correct, v2 vs baseline_k6 (primary) | 77 | 92.6% | 41.1% | +51.5% [+39.4%, +63.2%] | 45/2 | 1.6e-11 | — |
| H2 correct, v2 vs baseline_k12 | 77 | 92.6% | 55.4% | +37.2% [+25.1%, +49.4%] | 34/4 | 6e-07 | 6e-07 |
| H3 numeric accuracy, v2 vs baseline_k6 | 63 | 93.9% | 42.9% | +51.1% [+38.6%, +63.2%] | 40/2 | 4.1e-10 | 8.2e-10 |
| H4 citation support, v2 vs baseline_k6 | 70 | 94.0% | 44.2% | +49.7% [+38.6%, +60.8%] | 47/3 | 3.7e-11 | 1.1e-10 |

## Correct answers, attempt level [95% Wilson interval]

| slice | v2 | baseline_k6 | baseline_k12 |
|---|---|---|---|
| all | 93% [89%, 95%] (n=231) | 41% [35%, 48%] (n=231) | 55% [49%, 62%] (n=231) |
| portion: heldout | 92% [86%, 95%] (n=132) | 45% [37%, 54%] (n=132) | 58% [50%, 66%] (n=132) |
| portion: development | 94% [87%, 97%] (n=99) | 35% [27%, 45%] (n=99) | 52% [42%, 61%] (n=99) |
| comparative_prose | 76% [55%, 89%] (n=21) | 0% [0%, 15%] (n=21) | 14% [5%, 35%] (n=21) |
| cross_company | 100% [85%, 100%] (n=21) | 0% [0%, 15%] (n=21) | 0% [0%, 15%] (n=21) |
| cross_statement | 95% [77%, 99%] (n=21) | 19% [8%, 40%] (n=21) | 38% [21%, 59%] (n=21) |
| lookup | 100% [85%, 100%] (n=21) | 14% [5%, 35%] (n=21) | 57% [37%, 76%] (n=21) |
| mixed | 100% [85%, 100%] (n=21) | 57% [37%, 76%] (n=21) | 71% [50%, 86%] (n=21) |
| multi_step | 71% [50%, 86%] (n=21) | 71% [50%, 86%] (n=21) | 71% [50%, 86%] (n=21) |
| negative | 95% [77%, 99%] (n=21) | 14% [5%, 35%] (n=21) | 14% [5%, 35%] (n=21) |
| prior_year | 100% [85%, 100%] (n=21) | 52% [32%, 72%] (n=21) | 57% [37%, 76%] (n=21) |
| prose | 100% [85%, 100%] (n=21) | 95% [77%, 99%] (n=21) | 100% [85%, 100%] (n=21) |
| segment | 81% [60%, 92%] (n=21) | 29% [14%, 50%] (n=21) | 86% [65%, 95%] (n=21) |
| unanswerable | 100% [85%, 100%] (n=21) | 100% [85%, 100%] (n=21) | 100% [85%, 100%] (n=21) |

Run-to-run agreement: v2 95%, baseline_k6 96%, baseline_k12 99%
