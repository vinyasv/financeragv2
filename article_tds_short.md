# Keep the LLM Out of the Deterministic Steps

*Six guidelines for splitting LLM question-answering systems into probabilistic and deterministic steps, tested against naive RAG on 77 held-out questions about SEC filings.*

---

Asked for Intel's fiscal 2023 free cash flow, defined in the question as operating cash flow minus additions to property, plant and equipment, a naive retrieval-augmented generation (RAG) system answered −$11,757 million in all six runs. The correct figure is −$14,279 million [2]. It took capital spending from an adjusted table with a nearly identical label.

The search was repeatable. Its criterion was wrong. Three fields fix a named figure: line item, company and period. Naive RAG chose by closeness in meaning. The failure is common. On FinanceBench, GPT-4-Turbo with retrieval answered 81% of questions about company filings incorrectly or refused [1].

Tool calling, program-aided reasoning and text-to-SQL all move exact work out of the LLM. This article distils that into six guidelines and tests them.

I built a system that follows the guidelines (Figure 1). An LLM writes a plan. Code looks up tagged figures, does the arithmetic and searches the text. The LLM writes the answer from the results. The baseline is naive RAG with the same LLM and embeddings: one embedding search over all 33 reports, at a matched text budget of about 9,500 characters and at double that. It has no keyword search and no company filter. The test system has both, so part of the gap may come from them. Each system answered 77 held-out questions about 33 annual reports (10-Ks) from 11 semiconductor companies, three times. 44 questions concern four companies the system never saw during development. The full method is in the [repository](https://github.com/vinyasv/financeragv2/blob/main/METHOD.md).

![Figure 1: The test system's pipeline.](figures/fig1_pipeline.png)
*Figure 1. Blue steps use the LLM. Grey steps are code. In the dashed step, code fetches candidate rows, the LLM picks one and code returns its value. Image by author.*

## Guideline 1: Split the task into deterministic and probabilistic steps

Ask two questions of each step. Could two careful people with the same inputs give different acceptable outputs? Then the step needs judgement, and it goes to the LLM. If not, can it be implemented and checked directly? Then write it as code.

Finding a company's operating income mixes both. Deciding which row the question means needs judgement, because filings label it "Operating income", "Income from operations" or something longer. Returning that row's value is exact. In the test system, code fetches candidate rows, the LLM picks one from a numbered list and code returns the stored value.

**Limit.** Exact lookup needs a structured record. A value that appears only in prose falls back to retrieval.

## Guideline 2: Keep structured data structured

Flattening a table into text keeps its labels. It breaks the link between each value and its row, column, period and unit. If users will filter, count or calculate with a field, keep it in a table.

Under the SEC's Inline XBRL rule, each figure in a filing's financial statements carries a tag for its concept, period and segment [3]. The test system loads the tags into a table and embeds only the prose. On single-figure questions it found the required figure in 100% of answers. Naive RAG found it in 14%. It reported Microchip's research and development expense as $1,100 million, from a chunk that said "$1.10 billion". The table says $1,097.4 million.

**Limit.** Someone must write the loader. That is cheap for tagged filings and expensive for PDFs.

## Guideline 3: Give the LLM a closed list when the answer is in a known set

When the valid outputs form a known set, show the LLM the set and accept only its members.

Asked which of AMD's segments earned the most, the planning step invented "Client and Gaming" by merging two real segment names. It now plans only with the segments AMD reports.

**Limit.** Search queries are free text. No list covers them.

## Guideline 4: Validate LLM output with code

Put a code check between the LLM and every step that depends on exact values.

The test system rejects a plan that names a company, year or segment absent from the database, and returns it to the LLM with the error. It also discards a final answer that states a number absent from the workings and the question.

**Limit.** The number check is crude. It ignores sign and units, skips anything that looks like a year and cannot tell which label a number belongs to. It catches a number with no source. A real number under the wrong label passes. The code and a full list of its gaps are in the repository.

## Guideline 5: Measure and tune retrieval as rigorously as lookup

Prose questions need search, and search needs its own measurement.

In development, the test system trailed naive RAG on prose-only questions, 72% to 83%. Most of its passages started mid-sentence. Cutting at paragraph breaks, adding keyword search beside embedding search and searching each company separately closed the gap. On held-out prose questions it passed 100% of answers against 95%. Both comparisons are LLM-graded.

**Limit.** These fixes were tuned on this corpus. Another corpus needs its own measurement.

## Guideline 6: Test the grader before trusting its scores

An LLM grader is itself probabilistic. Test it on answers with known errors.

My first grader passed an answer with planted wrong dates in five of five trials. It checked claims against the filings and ignored the answer. Making it quote the answer before its verdict fixed this.

After the run, a second LLM planted one realistic error in each claim the grader had passed, and a third confirmed each edit. The grader caught 520 of 521. It also leaned toward failing: after one planted error, it failed 7% of the untouched claims in that answer.

**Limit.** LLMs planted the errors. Only a human check can show whether the grader fails correct answers phrased unusually.

## Results

The headline measure is required-figure coverage: the share of an answer's required figures that appear anywhere in it, within tolerance. Code computes it. Averaged over three runs and 63 held-out questions with required figures, coverage was 94% for the test system, 43% for naive RAG at the matched budget and 60% at double the budget. The gap over the matched baseline was 51 points (95% confidence interval: 39 to 63). On the four unseen companies it was 92% against 49%.

![Figure 2: Required figures found by question type for the test system and naive RAG at both text budgets.](figures/fig2_figures_found_by_type.png)
*Figure 2. Required figures found, by question type, scored by code. Most types have 7 questions, so differences between types are indicative. Image by author.*

The main limits:

- **No ablation.** The gain cannot be attributed to any single guideline.
- **A plain baseline.** Keyword search and a company filter would likely close part of the gap. The single-figure result (100% against 14%) depends least on this, because those figures came from the table.
- **Coverage is not correctness.** Code does not check which label a figure sits under, and the test system states more numbers (median 8 against 4). A post-hoc check requiring the grader to confirm each figure's label moved every system by 1 to 3 points and left the gap at 52.
- **No human check of the grader.** The pre-registered human review was not done. The mutation test in Guideline 6 stands in for part of it.
- **Narrow scope.** One domain, one answer LLM, 7 questions per type and an answer key written by LLMs with no expert review.

## Where the guidelines ran out

The grader failed 17 of the test system's 231 answers. Six were confident wrong answers from one gap.

Asked which Intel segment had the highest 2023 operating margin, the system named Client Computing Group at 32.51%. The answer, from the fiscal 2023 report, is Mobileye at 31.94%. Intel's fiscal 2024 report restates 2023 segment results and gives Client Computing $9,513 million of operating income. The fiscal 2023 report gives $6,520 million, a 22.28% margin. The system mixed the two reports. It still scored full coverage, because its workings stated the right figures. Only the grader caught the wrong conclusion. An Analog Devices question failed the same way, on reclassified revenue.

The lookup was exact. Its key, company and fiscal year, was incomplete: one year's figure can appear in three reports. A fix is to store each figure's source report and prefer the one the question names. I have not tested it.

In the other 11, a lookup or search found nothing and the system declined to answer. So structured lookup has two failure modes. A key that misses a distinction gives a confident wrong answer. A missing row gives an honest refusal.

## When to use it

Give the LLM the steps that need judgement. Give code the lookups and calculations you can specify and check. Then audit the rules code runs on: all six confident wrong answers here came from a missing source-selection rule.

Skip it when one prose passage answers most of your questions. The advantage was small or absent for prose-only, unanswerable and multi-step questions. At double the budget, naive RAG matched or beat the test system on prose and multi-step questions and found more segment figures, 86% against 81%. It was also faster: 5.1 seconds per answer against 9.3.

The code, questions, answer key, method and every system output are at https://github.com/vinyasv/financeragv2.

## References

[1] P. Islam et al., FinanceBench: A New Benchmark for Financial Question Answering (2023), arXiv:2311.11944

[2] Intel Corporation, Annual Report on Form 10-K for fiscal year 2023 (2024), SEC EDGAR. Net cash provided by operating activities: $11,471 million. Additions to property, plant and equipment: $25,750 million.

[3] U.S. Securities and Exchange Commission, Inline XBRL Filing of Tagged Data, Release No. 33-10514 (2018), sec.gov

All figures are by the author. Source data: 10-K filings from SEC EDGAR, public domain.
