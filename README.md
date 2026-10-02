# FinanceRAG v2

## Purpose

This repository contains an experiment. It is not a product.

The experiment tests one idea. The LLM writes a plan and the answer. Code finds the numbers and does the arithmetic. Does this system answer questions about SEC 10-K filings better than naive RAG?

On this test, the answer is yes, and the difference is large. But the test is small, and one person made it. No person checked the LLM grader. Read the limitations before you use a number from this test.

The article is in [article_tds_short.md](article_tds_short.md). The full method is in [METHOD.md](METHOD.md).

## How the system works

- **Numbers.** The system reads the numbers from the inline XBRL tags in each filing. Postgres keeps these numbers. The system finds a number by company, fiscal year, statement and segment. The LLM can select a row from a numbered list. The LLM does not write numbers. Python does all arithmetic.
- **Text.** The system finds text with hybrid search: pgvector and Postgres full-text search. Each passage is a full paragraph.
- **Plan and answer.** The LLM writes a small JSON plan. Then the LLM writes the answer from the numbers and the passages. Code rejects a plan that names a company, year or segment that is not in the database. Code removes a summary that contains a number that is not in the calculation.
- **Missing data.** If the system cannot find the data, it answers "insufficient". It does not guess.

The baseline is naive RAG. It divides each filing into chunks, does one vector search and makes one LLM call. It uses the same models as the system.

## Results

The test used 77 held-out questions about 33 10-K filings from 11 semiconductor companies. 44 of the questions are about 4 companies. I did not use these 4 companies during development. Each system answered each question 3 times.

| Measure | This system | Naive RAG, same text budget | Naive RAG, 2 × text budget |
|---|---|---|---|
| Required numbers found (code scores this) | 94% | 43% | 60% |
| Required numbers found, and the LLM grader agrees with the label | 92% | 40% | 57% |
| Pass rate: all numbers and claims (the LLM grader scores this) | 93% | 41% | 55% |
| Median time for one answer | 9.3 s | 5.1 s | 5.2 s |

The full tables are in `eval/heldout/results/`: `report.md`, `summary.md`, `sensitivity.md` and `mutation.md`.

## Limitations

- **Small test.** The test uses one domain and one answer model (`openai/gpt-6-luna`). Each question type has approximately 7 questions. Thus, the differences between question types are not reliable.
- **No human check of the grader.** The protocol included a human check of the LLM grader on 99 claims. Nobody did this check. The pass rate and the claim scores use this grader. The code-scored number match does not use it.
- **Mutation test of the grader.** After the run, an LLM put one error into each claim that the grader passed. The grader found 520 of 521 errors. But it also failed 7% of the correct claims near an error. LLMs made these errors, so this test does not replace a human check.
- **The LLM wrote the answer key.** LLM agents wrote and checked the questions and the answers. No financial expert examined them.
- **Weak pre-registration.** Before the run, I recorded SHA-256 hashes of the questions, code and analysis (`eval/heldout/FREEZE.sha256`). I did not publish these hashes before the run.
- **Simple baseline.** The baseline has no keyword search and no company filter. A better baseline can possibly close part of the difference.
- **No ablation.** The test does not show which part of the system causes the improvement.
- **A found number is not a correct answer.** For one Intel question, the system showed the correct numbers for each segment. Then it named the wrong segment in all 3 runs.
- **Known error.** The system finds a number by company and fiscal year. But a later report can change the numbers for an earlier year. Thus, the system can mix numbers from two reports and give a wrong answer. This error caused 6 of the 17 failures. The error is not repaired.
- **Not better on all question types.** On text, multi-step and unanswerable questions, the results were approximately equal. On segment questions, naive RAG with 2 × the text budget found more numbers (86% against 81%). The system is also slower and makes more model calls (2.8 against 2.0).
- **Development tuning.** I changed the system after failures on 54 development questions (`eval/results_summary.md`). Thus, the development scores are too high. The held-out test is the real test.
- **Scope.** The system reads only HTML filings with inline XBRL. Only the tagged numbers in tables are exact. The system finds all other data with search. Citations show table rows and passages, not page numbers. The repository has only one test. This test uses live services.
- **AI help.** I made the system and the question pipeline with help from an AI coding assistant.

## How to run the system

You need:

- Python 3.
- A Postgres database with `pgvector`. You can use Supabase.
- An OpenRouter API key.

NOTE: The code imports itself as the package `v2`. Thus, the folder must have the name `v2`. Run all commands from the parent folder.

1. Clone the repository into a folder with the name `v2`:

   ```bash
   git clone https://github.com/vinyasv/financeragv2.git v2
   ```

2. In the parent folder, make a file with the name `.env`. Put your API key and database URI in this file:

   ```text
   OPENROUTER_API_KEY=...
   V2_DATABASE_URL=postgresql://...
   ```

   NOTE: If you use Supabase and your network does not have IPv6, use the session pooler URI.

3. Install the dependencies:

   ```bash
   python3 -m pip install -r v2/requirements.txt
   ```

4. Make the database tables:

   ```bash
   python3 -m v2.app init
   ```

5. If you use Supabase, run `security.sql` in the Supabase SQL editor. This file turns on Row-Level Security. Then the public REST API cannot read or change the tables. The system connects as the table owner, so it continues to operate.

   CAUTION: Do step 5 again after you reset the tables. Also do step 5 after the first baseline ingest, because the baseline makes a new table.

6. Download the filings from SEC EDGAR. To download the held-out filings, add `--heldout`.

   ```bash
   python3 -m v2.eval.fetch_filings
   ```

7. Ingest one filing:

   ```bash
   python3 -m v2.app ingest v2/eval/sources/nvda-20240128.htm --id nvda-fy2024 --company NVIDIA --url https://www.sec.gov/Archives/edgar/data/1045810/000104581024000029/nvda-20240128.htm
   ```

8. Ask a question:

   ```bash
   python3 -m v2.app ask "Calculate NVIDIA's FY2024 operating-cash-flow margin."
   ```

## Evaluation

- `eval/heldout/FREEZE.md` contains the commands for the held-out run.
- `eval/run.py` runs the systems, grades the answers and calculates the scores.
- `eval/analysis.py` calculates the pre-registered statistics.
- `eval/sensitivity.py` does the label check. I added this check after the run.
- `eval/judge_mutation.py` does the mutation test of the grader. I added this test after the run.
- To run the end-to-end test, use this command: `python3 -m pytest v2/test_e2e.py -q`.

## Files

| Path | Contents |
|---|---|
| `app.py`, `xbrl.py`, `reasoning.py`, `schema.sql` | The system |
| `security.sql` | Turns on Row-Level Security for Supabase |
| `eval/baseline.py` | The naive RAG baseline |
| `eval/heldout/` | The protocol, the frozen questions, the adjudication log and the results |
| `eval/questions_*.jsonl`, `eval/results/` | The development questions and their runs |
| `METHOD.md` | The full method: questions, freeze, models, grading and statistics |
| `GOALS.md` | The initial goals and design decisions |
| `figures/` | The article figures and the scripts that make them |
