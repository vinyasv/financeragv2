# Held-out evaluation protocol (pre-registration)

Status: **FROZEN, awaiting author sign-off** (see `FREEZE.md`). It becomes binding when the author signs. No system is run on the held-out questions before that.

## 1. Purpose and hypotheses

We test whether FinanceRAG v2 answers questions over SEC 10-K filings more accurately than a naive retrieval-augmented baseline. The test uses questions and filings that played no part in developing v2.

- **H1 (primary).** v2's full-answer correctness is higher than the budget-matched baseline's (`k=6`).
- **H2.** v2's full-answer correctness is higher than the generous-budget baseline's (`k=12`).
- **H3.** v2's numeric accuracy is higher than the budget-matched baseline's.
- **H4.** v2's citation support is higher than the budget-matched baseline's.

H2–H4 are secondary. Results per category are descriptive only; no hypothesis is tested per category.

## 2. Development history (disclosure)

v2 was developed and repeatedly corrected against a 54-question development set over 21 filings (`../questions_*.jsonl`, `../results_summary.md`). Several fixes were derived from failures in that set, so development-set scores are optimistic. This held-out evaluation is the confirmatory test. Development-set results must not be pooled with it.

## 3. Systems under test (frozen at sign-off)

All arms use the same answer model (`openai/gpt-6-luna`, temperature 0), the same embedding model (`openai/text-embedding-3-small`), the same database, and exact vector search. Code is frozen by the SHA-256 hashes recorded in section 11.

| Arm | Description |
|---|---|
| `v2` | The system in `v2/app.py`, `v2/xbrl.py`, `v2/reasoning.py`, `v2/schema.sql` |
| `baseline_k6` | Naive RAG (`v2/eval/baseline.py`): whole-filing chunks, one vector search, top 6, one chat call |
| `baseline_k12` | The same with top 12 |

`k=6` was fixed in advance from the development set, where v2 retrieved a mean of 10,470 characters against a mean baseline chunk of 1,605 characters. It is not re-tuned on held-out data. Actual evidence sizes are reported.

## 4. Corpus

- **Filings:** the 21 development filings (`../filings.json`) plus 12 held-out filings (`filings.json` here). The held-out filings cover Analog Devices, Marvell, ON Semiconductor and Microchip, fiscal years 2022–2024. They were downloaded from SEC EDGAR and are identified by SHA-256.
- **Search scope:** every arm searches all 33 filings. The development filings serve as distractors.
- **No inspection before freeze:** no one developing v2 parses, inspects or tunes anything on the held-out filings before the freeze. Ingestion is part of the frozen run. An ingestion failure is a result: every attempt on that filing is scored incorrect for the affected arm.

## 5. Question set

- **Size and structure:** 77 questions, 7 in each of 11 categories: `lookup`, `cross_statement`, `cross_company`, `prior_year`, `segment`, `negative`, `prose`, `comparative_prose`, `mixed`, `multi_step`, `unanswerable`. About half the questions in each category concern held-out companies. The rest cover development companies but are new questions, not duplicates of the development set.
- **Blinding:** questions are written by agents that cannot read any system code, any results, any development-set failure analysis, or any system description. They may read the filings, the manifests, this protocol, and the development questions (to avoid duplicates only).

**Writing rules**

1. **Name everything.** Name the company, the fiscal year, and the filing where it matters. For non-calendar fiscal years, give the period end date, e.g. "fiscal 2024 (ended February 3, 2024)".
2. **Define computed metrics** in the question, e.g. "free cash flow, defined as net cash provided by operating activities minus purchases of property and equipment".
3. **State the expected sign or direction** whenever a value could reasonably be reported either way, e.g. "report the change as a signed percentage" or "report capital expenditures as a positive amount".
4. **One reading only.** A question must have a single defensible answer from the filings. Otherwise drop it.
5. **Unanswerable questions** must be genuinely unanswerable from all 33 filings. Later filings' comparative columns include earlier years, so check those. Use 7 plausible questions: companies outside the corpus, periods outside the corpus, or metrics the filings do not disclose.

**Gold numbers** (`gold`)

- **Only the numbers the question explicitly asks for.** Inputs used to compute them are not gold. They go in `gold_sources` for retrieval measurement, so an answer reaching the right result by a different valid path is not penalised.
- **Money** is given in USD millions as printed, tolerance 0.5.
- **Percentages** are given as percent numbers, tolerance 0.05 percentage points. **Ratios** have tolerance 0.005.
- **Rounding:** computed values are calculated from printed figures and rounded to 2 decimals. If the question asks for coarser rounding, the tolerance follows.
- **Rounding paths:** a derived value's tolerance is widened, where needed, to also accept the result obtained by rounding each intermediate value to 2 decimals before the final step. This means the grade depends on the answer, not on the rounding path. The adjudicator applies this to every derived value before freeze.

**Claims** (`claims`): the non-numeric content a correct answer must state. The rules:

- **Atomic:** one fact per claim.
- **Asked for:** only what the question asks.
- **Meaning, not wording:** phrase by meaning, never requiring exact filing language.
- **Neutral:** do not require the answer to attribute a fact to a particular speaker or holder of an expectation unless the question asks who said it.
- **"What drove it" questions:** require the primary driver or drivers the filing states (at most two claims). Do not require secondary details, amounts or examples unless the question asks for them.
- **"Which / name all" questions:** require each named item the filing gives.
- **Identification questions** ("which segment grew fastest"): include a claim that the answer identifies the item.

**Sources** (`gold_sources`): each needed printed number (digits and commas as printed) or a short exact phrase from the filing, with its company. These are used only for the retrieval proxy (source recall).

## 6. Verification and adjudication (before freeze)

1. **Independent answers.** A verifier agent receives only the question texts. It answers each from the filings and records its values and the facts it relied on.
2. **Comparison.** The verifier's numbers are compared with the gold automatically. The verifier then reviews each claim against rules 5.1–5.5 and the rubric rules.
3. **Adjudication.** An adjudicator agent, also blind to systems, resolves every disagreement by reading the filing. It then corrects the gold, rewrites the question to remove ambiguity, or drops the question.
4. **Log.** Every change and drop is logged in `adjudication.jsonl`. Dropped questions are not replaced after freeze. The final count is reported.
5. **No later edits.** After freeze, no question, gold value, claim or tolerance may change. Errors found later are reported as errata alongside results computed on the frozen set.

## 7. Run procedure

1. **Ingest** the 12 held-out filings into both the v2 and baseline stores: `run.py ingest --manifest heldout/filings.json`.
2. **Answer:** each arm answers each question 3 times, with 4 workers, on a machine prevented from sleeping (`caffeinate`, on mains power).
3. **Infrastructure errors** (database or network connection errors) are retried once automatically. Remaining ones are re-run with `run.py retry`, and their count is reported. Any other exception is a system failure, scored incorrect.
4. **Grade:** all attempts are graded by the same judge after all arms have finished.

## 8. Scoring

- **Numeric match.** A gold number is matched if a number parsed from the answer lies within tolerance, plus 1e-9 for floating-point noise. A number followed by "billion" or "thousand" is also compared after conversion to millions, since gold money is in USD millions.
- **Claims.** A claim is stated if the judge's outcome is `stated`. The judge quotes the answer, gives a reason, then returns `stated`, `contradicted` or `missing`, judged from the answer alone.
- **Correct** (primary metric):
  - **Answerable questions:** every gold number is matched and every claim is stated.
  - **Unanswerable questions:** the answer declines ("insufficient evidence") without giving a fabricated answer.
- **Numeric accuracy:** the fraction of gold numbers matched.
- **Citation support:** the fraction of all required items (gold numbers and claims) that are stated and supported by the evidence the answer cites, as judged.
- **Source recall:** a retrieval proxy based on exact source text; it is not a support measure.
- **Also reported:** evidence characters, crash rate, run-to-run agreement, latency and API calls.
- **Judge:** `google/gemini-3.8-flash`, temperature 0, with the prompt frozen by hash (section 11). Empty or malformed judge output is retried up to 3 times. An attempt still unjudged is re-run with `run.py judge`. A persistent failure is reported and that attempt is excluded from the claim-level metrics only.

## 9. Judge validation

1. **Planted errors.** Before any held-out run, the judge is tested on 5 fixed planted-error cases from the development set, twice each (`analysis.py judge-check`). The pre-specified pass criterion is that all planted claims are failed and all unedited answers passed.
2. **Human audit.** After grading, a random sample of 99 judged claims is drawn: 33 per arm, fixed seed, rows shuffled (`analysis.py audit-sample`). The arm is hidden. Each claim is labelled by a human author for `stated` and `supported` (`analysis.py audit-score`), and we report the agreement and Cohen's kappa between human and judge.
3. **Reporting threshold.** If kappa for `stated` is below 0.6, judged metrics are reported as unreliable, and only numeric accuracy, which is computed without the judge, supports H1.

## 10. Statistical analysis (script: `../analysis.py`, frozen at sign-off)

- **Unit of analysis:** the question. Each question's score per arm is its mean correctness over the 3 runs.
- **Primary test (H1):** the paired difference in mean per-question score, v2 minus `baseline_k6`.
  - A 95% confidence interval comes from a paired bootstrap over questions (10,000 resamples, seed 20260925).
  - The significance test is an exact two-sided sign test on per-question differences, ties dropped.
  - α = 0.05.
- **Secondary tests (H2–H4):** the same method, with Holm–Bonferroni correction across the three.
- **Descriptive results:**
  - by category and by corpus portion (held-out companies vs development companies);
  - 95% Wilson intervals on attempt-level proportions;
  - run-to-run agreement.
- **Full disclosure:** all metrics for all arms are reported, whatever the outcome.

## 11. Freeze record

`FREEZE.md` holds the code and data hashes, models, parameters, the exact run commands, and the author's sign-off. Before running, `shasum -a 256 -c FREEZE.sha256` must pass.

## 12. Threats to validity

- **Test authors:** questions and gold were written by LLM agents rather than domain experts. Independent verification and adjudication reduce errors but not question-selection bias. A human expert review of a sample is recommended before publication.
- **Same model:** both systems use the same answer model, so the comparison isolates retrieval and reasoning design, not model capability.
- **LLM judge:** judged metrics depend on an LLM judge. Section 9 bounds this.
- **Narrow corpus:** one industry (semiconductors) and one form type (10-K). Generalisation beyond these is not tested.
- **Development overlap:** the system's authors know the development set. Held-out questions on development companies share the corpus, but not the questions, with development.
