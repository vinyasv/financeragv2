# FinanceRAG v2 goals

## Product goal

Answer questions over real financial filings with enough evidence for a reader to check every claim and number. Optimize for correctness and clear provenance before speed or feature count.

## First end-to-end milestone

1. Ingest the original SEC HTML filings for NVIDIA FY2024 and AMD FY2024, preserving text, tables, document identity, and source URL.
2. Store passages and embeddings in **one managed Postgres database with pgvector**. Re-ingesting a filing replaces its old passages without duplicates.
3. Use **OpenRouter** for both embeddings and answer generation. A small plan names each required operand and its source statement; there is no agent DAG, generated SQL, or reranker.
4. Return an answer with passage citations. If the retrieved evidence is insufficient, say so.
5. Run an end-to-end test against the two real filings and live services. The test asks for facts from multiple statements and checks both the answer and its cited evidence.

## Evaluation goals

- Measure full-answer correctness, required-source recall, citation support, latency, and API calls.
- Compare against a one-search vector baseline with the same corpus, model, embedding model, retrieval budget, and question set.
- Prewrite questions and expected values before running either system. Use enough filings that the baseline cannot see all relevant evidence in one context window.
- Make no superiority claim from a tiny corpus or a single stochastic run.

## Design constraints

- Keep the code small and explicit. One ingestion path, one database, one model gateway, one query path.
- Keep the original repo intact during the rebuild.
- Add only end-to-end tests for user-visible behavior. No tests that simply mirror internal functions.
- Perform arithmetic in Python from source-checked numbers. The LLM may plan a formula and identify a cited source number, but it does not supply the result.

## Outside the first milestone

PDF and spreadsheet ingestion, a UI, arbitrary SQL generation, background jobs, multiple database backends, and generalized agent planning.

## Decision log

- SEC HTML first: it is the original source for the filings already in this repo and preserves tables more directly than PDF text extraction.
- Supabase Postgres with pgvector is the managed deployment. Prose passages live in the vector-backed table; financial table rows, labels, periods, and numeric cells live in a separate relational table. Both are in one managed Postgres project to keep the code and setup small.
- OpenRouter model defaults: `openai/gpt-6-luna` for generation and `openai/text-embedding-3-small` (1536 dimensions) for embeddings.
- Numeric facts come from inline XBRL, not from parsing table text: XBRL gives the sign, scale, period and segment of every number, so a fact is looked up by company, fiscal year and statement instead of being copied out of a row by the model.
- One bounded re-plan: a plan may first list candidate rows (for example, each segment's revenue) and then plan once more. This is the smallest step that supports "find X, then use X" questions; there is no general agent loop.
- Evaluation corpus: 21 10-Ks (seven semiconductor companies, fiscal years 2022–2024), so the one-search baseline cannot see every relevant table at once.
- Prose retrieval, after tracing eval failures: passages were fragmented (63% started mid-sentence) and one 4-passage vector search missed answering passages. Passages are now whole paragraphs. Search is hybrid (vector plus Postgres full text, fused by reciprocal rank) with neighbouring passages, over two queries per company. Answers state their conclusion first; "largest or smallest" is picked in Python, and a summary is kept only if every number in it appears in the workings.
