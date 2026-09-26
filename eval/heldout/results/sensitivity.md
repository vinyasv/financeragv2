# Sensitivity: required figures bound to their label (post-hoc)

Loose is the frozen metric (`run.score()["numeric"]`). Strict also requires the judge's verdict on that
figure's claim to be "stated". Strict therefore depends on the LLM judge, which the human audit has not
validated. Unit: question, mean over runs, questions with gold figures only.

| comparison | questions | v2 | comparator | difference [95% bootstrap CI] | wins/losses | p (sign test) | p (Holm) |
|---|---|---|---|---|---|---|---|
| loose (frozen), v2 vs baseline_k6 | 63 | 93.9% | 42.9% | +51.1% [+38.6%, +63.2%] | 40/2 | 4.1e-10 | 1.6e-09 |
| strict, v2 vs baseline_k6 | 63 | 92.3% | 40.0% | +52.3% [+39.9%, +64.5%] | 42/3 | 8.7e-10 | 2.6e-09 |
| loose (frozen), v2 vs baseline_k12 | 63 | 93.9% | 59.5% | +34.4% [+20.6%, +47.9%] | 29/4 | 1.1e-05 | 2.2e-05 |
| strict, v2 vs baseline_k12 | 63 | 92.3% | 56.7% | +35.6% [+21.3%, +49.6%] | 31/5 | 1.3e-05 | 2.2e-05 |

## By slice (question-level mean, loose → strict)

| slice | v2 | baseline_k6 | baseline_k12 |
|---|---|---|---|
| all | 94% → 92% | 43% → 40% | 60% → 57% |
| portion: heldout | 92% → 89% | 49% → 47% | 64% → 64% |
| portion: development | 97% → 97% | 34% → 30% | 53% → 46% |
| comparative_prose | 75% → 75% | 50% → 50% | 62% → 62% |
| cross_company | 100% → 100% | 14% → 13% | 14% → 8% |
| cross_statement | 95% → 95% | 26% → 26% | 45% → 45% |
| lookup | 100% → 100% | 14% → 14% | 57% → 57% |
| mixed | 100% → 100% | 57% → 43% | 71% → 57% |
| multi_step | 86% → 71% | 86% → 76% | 100% → 95% |
| negative | 98% → 98% | 26% → 26% | 26% → 26% |
| prior_year | 100% → 100% | 52% → 52% | 57% → 57% |
| prose | 100% → 100% | 89% → 89% | 100% → 100% |
| segment | 81% → 81% | 43% → 43% | 86% → 86% |
| unanswerable | - | - | - |

Pooled over all gold figures and attempts (loose → strict): v2 93.7% → 92.7%, baseline_k6 40.3% → 38.3%, baseline_k12 54.1% → 51.5%

## Figures matched by number but not stated by the judge

| arm | question | run | figure | judge quote |
|---|---|---|---|---|
| v2 | h053 | 1 | AMG 2024 segment gross margin % = 1,306.3 / 2,609.1: 50.07 | AMG had the highest 2024 segment gross margin: **50.10%**. |
| v2 | h053 | 2 | AMG 2024 segment gross margin % = 1,306.3 / 2,609.1: 50.07 | Context: AMG had the highest 2024 segment gross margin: **50.10%**. |
| v2 | h053 | 3 | AMG 2024 segment gross margin % = 1,306.3 / 2,609.1: 50.07 | Context: **AMG** had the highest 2024 segment gross margin: **50.1%**. |
| baseline_k6 | h042 | 2 | Micron FY2022 gross margin % = 13,898 / 30,758 (= (30,758 - 16,860) / 30,758): 45.18 | Micron’s fiscal 2022 gross margin percentage was **45.19%**, calculated as $13,898 million ÷ $30,758 million × 100. |
| baseline_k6 | h047 | 3 | AMD 2023 operating margin % = 401 / 22,680: 1.77 | operating margin was **$401 million ÷ $22,700 million = 1.77%** |
| baseline_k6 | h048 | 1 | NVIDIA FY2024 gross margin % = (60,922 - 16,621) / 60,922: 72.72 | Fiscal 2024 gross margin was **72.7%**: revenue was 100.0% and cost of revenue was 27.3% of revenue, so gross margin = ( |
| baseline_k6 | h048 | 2 | NVIDIA FY2024 gross margin % = (60,922 - 16,621) / 60,922: 72.72 | (none) |
| baseline_k6 | h053 | 2 | AMG 2024 segment gross margin % = 1,306.3 / 2,609.1: 50.07 | AMG had the highest 2024 segment gross margin: **50.06%** ( $1,306.3 million ÷ $2,609.1 million × 100 ). |
| baseline_k6 | h053 | 3 | AMG 2024 segment gross margin % = 1,306.3 / 2,609.1: 50.07 | AMG had the highest 2024 segment gross margin: **50.06%**, calculated as $1,306.3 million ÷ $2,609.1 million. |
| baseline_k12 | h041 | 1 | TI 2024 FCF margin % = (6,318 - 4,820) / 15,641: 9.58 | Texas Instruments’ free cash flow was $1,498 million and revenue was $15,641 million, giving a margin of **$1,498 ÷ $15, |
| baseline_k12 | h042 | 1 | Micron FY2022 gross margin % = 13,898 / 30,758 (= (30,758 - 16,860) / 30,758): 45.18 | Its gross margin percentage was **45.19%** (13,898 ÷ 30,758 × 100). |
| baseline_k12 | h042 | 2 | Micron FY2022 gross margin % = 13,898 / 30,758 (= (30,758 - 16,860) / 30,758): 45.18 | Micron’s 2022 gross margin percentage was **45.19%**: $13,898 million ÷ $30,758 million × 100 |
| baseline_k12 | h042 | 3 | Micron FY2022 gross margin % = 13,898 / 30,758 (= (30,758 - 16,860) / 30,758): 45.18 | Micron’s fiscal 2022 gross margin percentage was **45.19%**: $13,898 million ÷ $30,758 million × 100 |
| baseline_k12 | h048 | 1 | NVIDIA FY2024 gross margin % = (60,922 - 16,621) / 60,922: 72.72 | Fiscal 2024 gross margin was **72.7%**: using the income statement’s percentages, \((100.0\% \text{ revenue} - 27.3\% \t |
| baseline_k12 | h048 | 2 | NVIDIA FY2024 gross margin % = (60,922 - 16,621) / 60,922: 72.72 | Fiscal 2024 gross margin was **72.7%**: \((100.0\%-27.3\%)/100.0\%=72.7\%\) |
| baseline_k12 | h048 | 3 | NVIDIA FY2024 gross margin % = (60,922 - 16,621) / 60,922: 72.72 | (none) |
| baseline_k12 | h055 | 3 | Graphics FY2023 operating margin % = 4,552 / 11,906: 38.23 | $4,552 million ÷ $11,906 million = **38.22%** |
