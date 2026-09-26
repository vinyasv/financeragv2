# FinanceRAG v2

Read [GOALS.md](GOALS.md) first. This is the first vertical slice, not a replacement for the existing CLI yet.

## How it works

Ingestion splits each SEC 10-K HTML filing by type:

- **Numeric facts** (`v2_facts`) come from the filing's inline XBRL. Each fact has its sign, scale (money in USD millions), fiscal year, period, segment dimensions, and the statement its table belongs to (income, cash flow, balance sheet, equity, comprehensive, segment, other). Its citation is the printed table row (`v2_table_rows`).
- **Prose passages** (`v2_passages`) are chunked by 10-K item and embedded. Tables without tagged numbers are embedded as passages too.

Prose passages pack whole paragraphs into ~1,800 characters without splitting sentences. Each is embedded with its company, fiscal year and 10-K item.

A question gets a small JSON plan:

- **Numbers:** found by fixed SQL on company, fiscal year, statement and segment, then ranked by row label and XBRL concept. The model picks a numbered candidate only when the ranking has no clear winner; it never copies a number. Arithmetic runs in Python `Decimal`, and so does picking the largest or smallest item ("which segment grew fastest").
- **Prose:** searched per company with two queries (the question, and the way a filing would phrase the answer). Vector and Postgres full-text rankings are fused, and the neighbours of the best hits are included.
- **Discovery:** if the answer depends on something unknown in advance, the plan first lists matching rows, then plans once more using only the listed segments.
- **Answer:** a short summary states the conclusion first, followed by the cited workings. A summary containing any number that isn't in the workings or retrieved text is dropped.
- **Missing evidence:** reported as `insufficient` rather than guessed.

## Setup

Create a managed Postgres database (Supabase is the intended host) with `pgvector` available. Use Supabase's **Session pooler** connection URI if the direct database host is unreachable over IPv6. Put the URI in the repository root `.env`:

```text
OPENROUTER_API_KEY=...
V2_DATABASE_URL=postgresql://...
```

Install dependencies from the repository root:

```bash
python3 -m pip install -r v2/requirements.txt
python3 -m v2.app init
```

`init --reset` drops and recreates the v2 tables. Use it after a schema change, then ingest again.

## Ingest and ask

```bash
python3 -m v2.app ingest v2/eval/sources/nvda-20240128.htm --id nvda-fy2024 --company NVIDIA --url https://www.sec.gov/Archives/edgar/data/1045810/000104581024000029/nvda-20240128.htm
python3 -m v2.app ask "Calculate NVIDIA's FY2024 operating-cash-flow margin."
```

Re-ingesting an unchanged file with the same parser version is skipped. Otherwise the filing's old rows are replaced in one transaction.

## Evaluation against a naive baseline

The corpus is 21 10-Ks: NVIDIA, AMD, Intel, Qualcomm, Broadcom, Micron and Texas Instruments, fiscal years 2022–2024. The questions (`v2/eval/questions_*.jsonl`, 54 in total), their hand-checked gold numbers and their required claims were written before either system was run. The baseline (`v2/eval/baseline.py`) flattens each whole filing, tables included, into chunks. It does one exact vector search (top `k`) and one chat call with the same models. Run it at `k=12` (more context than v2 gets) and at a `k` matched to v2's mean evidence size.

```bash
python3 -m v2.eval.fetch_filings           # optional SEC_USER_AGENT in .env
python3 -m v2.eval.run ingest --arm both
python3 -m v2.eval.run eval --arm v2 --runs 3
python3 -m v2.eval.run eval --arm baseline --k 12 --runs 3
python3 -m v2.eval.run retry v2/eval/results/<file>.json   # re-run attempts that hit a network or database error
python3 -m v2.eval.run judge v2/eval/results/<file>.json ...
python3 -m v2.eval.run summarize v2/eval/results/<file>.json ...
```

Scoring:

- **Numbers:** parsed from the answer and matched to the gold values within tolerance.
- **Other claims:** each question lists the non-numeric claims a full answer must make, such as a date, an identification ("Data Center grew fastest") or a stated driver. A judge model (`V2_JUDGE_MODEL`, default `google/gemini-3.8-flash`, a different family from the system under test; it agreed with `claude-sonnet-5` on 95.6% of claims) decides whether the answer commits to each claim. It also decides whether the evidence the answer cites supports each claim.
- **Correct:** every gold number matched and every other claim stated. For unanswerable questions, the answer declines with "insufficient evidence".
- **Citation support:** the share of all required claims (numbers included) that are stated and supported by cited evidence.
- **Source recall:** the gold source text appears in retrieved evidence. It is an exact-wording proxy for retrieval, not a support check.
- **Also reported:** evidence size (the retrieval budget), crash rate, run-to-run agreement, latency and API calls.

Results files also store each plan and any discovered rows, so failures can be traced.

## End-to-end test

```bash
python3 -m pytest v2/test_e2e.py -q
```

One live test over the two FY2024 filings. It covers a cross-company calculation, a negative value, a prior-year value, a segment share, prose comparing two companies, a mixed question, a question answered after the discovery step, and an unanswerable question.

Current limitations:

- HTML only.
- Numeric facts are limited to numbers tagged in inline XBRL inside tables.
- Planning, and the choice between close candidates, still depend on the LLM.
- Citations identify table rows or passages, not page numbers.
