# FinanceRAG v2

An experiment, not a product. It asks one question: if the LLM only plans and writes, and code does the lookups and arithmetic, does it answer questions about SEC 10-K filings better than naive RAG?

On this test it did, by a wide margin. The test is small, one person built it and parts of the grading were never validated. Read the limitations before quoting any number. The write-up is in [article_tds_short.md](article_tds_short.md).

## What it does

- **Numbers** come from the filing's inline XBRL tags, stored in Postgres and looked up by company, fiscal year, statement and segment. The LLM may pick between numbered candidate rows. It never types a number. Arithmetic runs in Python.
- **Prose** is found by hybrid search (pgvector plus Postgres full text) over whole-paragraph passages.
- **The LLM** writes a small JSON plan, then an answer from the looked-up values and passages. Code rejects plans that name companies, years or segments not in the database. It drops a summary containing a number that isn't in the workings.
- **Missing evidence** is answered "insufficient", not guessed.

The baseline is naive RAG: whole filings chunked, one vector search, one LLM call, the same models.

## Result

77 held-out questions over 33 10-Ks from 11 semiconductor companies. 44 of the questions are about 4 companies never used in development. Each system answered every question 3 times.

| | this system | naive RAG, same text budget | naive RAG, 2× budget |
|---|---|---|---|
| Required figures found (code-scored) | 94% | 43% | 60% |
| Same, figure's label also confirmed by the LLM grader | 92% | 40% | 57% |
| Pass rate (all figures and claims; LLM-graded) | 93% | 41% | 55% |
| Median latency | 9.3 s | 5.1 s | 5.2 s |

Full tables: `eval/heldout/results/report.md`, `summary.md` and `sensitivity.md`.

## Limitations

- **Small and narrow.** One domain, one answer model (`openai/gpt-6-luna`), about 7 questions per type. Differences between question types are indicative, not established.
- **Unvalidated grader.** The pre-registered human check of the LLM grader (99 claims) was not done. Pass rates, claim scores, citation support and the label-confirmed figure score all depend on that grader. Only the plain figure match does not.
- **LLM-written answer key.** LLM agents wrote and cross-checked the questions and gold answers. No domain expert reviewed them.
- **Weak pre-registration.** Questions, code and analysis were hashed before the run (`eval/heldout/FREEZE.sha256`). The freeze was not published or signed off in advance.
- **No ablation.** The gain can't be attributed to XBRL lookup, planning, validation or anything else in particular.
- **Figures found ≠ correct.** On an Intel question the system listed the right segment's figures, then named the wrong segment in all three runs.
- **A known wrong-answer bug.** Lookups key on company and fiscal year. Later reports restate earlier years, so the system can mix figures from two reports and answer confidently and wrongly. This caused 6 of its 17 failures. Not fixed.
- **Not better everywhere.** It tied naive RAG on prose, multi-step and unanswerable questions. On segment questions it lost to naive RAG at 2× budget (81% vs 86% of figures found). It is slower and makes more model calls (2.8 vs 2.0).
- **Tuned on its development set.** Fixes came from failures on 54 development questions (`eval/results_summary.md`), so development scores are optimistic. The held-out set is the real test.
- **Scope.** Only HTML filings with inline XBRL. Only tagged table numbers are exact; everything else is retrieval. Citations point to table rows and passages, not page numbers. The only test is one live end-to-end test.
- **Built with an AI coding assistant**, including the question-generation pipeline.

## Running it

The code imports itself as `v2`, so clone it into a folder with that name and run commands from the parent folder:

```bash
git clone https://github.com/vinyasv/financeragv2.git v2
```

You need a Postgres database with `pgvector` (Supabase works; use its session pooler URI if IPv6 fails) and an OpenRouter key. Put both in a `.env` file in the parent folder:

```text
OPENROUTER_API_KEY=...
V2_DATABASE_URL=postgresql://...
```

Then install, create the tables, download filings and ask a question:

```bash
python3 -m pip install -r v2/requirements.txt
python3 -m v2.app init
python3 -m v2.eval.fetch_filings             # add --heldout for the held-out filings
python3 -m v2.app ingest v2/eval/sources/nvda-20240128.htm --id nvda-fy2024 --company NVIDIA --url https://www.sec.gov/Archives/edgar/data/1045810/000104581024000029/nvda-20240128.htm
python3 -m v2.app ask "Calculate NVIDIA's FY2024 operating-cash-flow margin."
```

The exact held-out run commands are in `eval/heldout/FREEZE.md`. Evaluation code is in `eval/run.py` (run, grade, score) and `eval/analysis.py` (pre-registered statistics). `eval/sensitivity.py` holds the label check added after the run. The end-to-end test runs with `python3 -m pytest v2/test_e2e.py -q`.

## Files

| path | what |
|---|---|
| `app.py`, `xbrl.py`, `reasoning.py`, `schema.sql` | the system |
| `eval/baseline.py` | naive RAG baseline |
| `eval/heldout/` | protocol, frozen questions, adjudication log, results |
| `eval/questions_*.jsonl`, `eval/results/` | development set and its runs |
| `GOALS.md` | original goals and design decisions |
| `figures/` | article figures and the scripts that draw them |
| `METHOD.md` | full method behind the article: questions, freeze, models, grading, statistics |
