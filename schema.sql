CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS v2_filings (
    id text PRIMARY KEY,
    company text NOT NULL,
    source_url text NOT NULL,
    content_sha256 text NOT NULL,
    parser_version integer NOT NULL,
    cik text NOT NULL,
    form_type text NOT NULL,
    fiscal_year integer NOT NULL
);

CREATE TABLE IF NOT EXISTS v2_passages (
    id text PRIMARY KEY,
    filing_id text NOT NULL REFERENCES v2_filings(id) ON DELETE CASCADE,
    kind text NOT NULL,
    section text NOT NULL,
    content text NOT NULL,
    embedding vector(1536) NOT NULL,
    tsv tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED
);

CREATE INDEX IF NOT EXISTS v2_passages_tsv_idx ON v2_passages USING gin (tsv);
-- Exact vector search: company/year filters would starve an approximate index at this size.
CREATE INDEX IF NOT EXISTS v2_passages_filing_id_idx ON v2_passages(filing_id);

-- Table rows are the human-readable citation for each numeric fact.
CREATE TABLE IF NOT EXISTS v2_table_rows (
    id text PRIMARY KEY,
    filing_id text NOT NULL REFERENCES v2_filings(id) ON DELETE CASCADE,
    statement text NOT NULL,
    row_label text NOT NULL,
    content text NOT NULL
);

CREATE INDEX IF NOT EXISTS v2_table_rows_filing_id_idx ON v2_table_rows(filing_id);

-- One inline-XBRL number: signed, scaled, and tied to one period.
CREATE TABLE IF NOT EXISTS v2_facts (
    id text PRIMARY KEY,
    filing_id text NOT NULL REFERENCES v2_filings(id) ON DELETE CASCADE,
    row_id text NOT NULL REFERENCES v2_table_rows(id) ON DELETE CASCADE,
    concept text NOT NULL,
    row_label text NOT NULL,
    statement text NOT NULL,
    period_start date,
    period_end date NOT NULL,
    period_type text NOT NULL,
    fiscal_year integer NOT NULL,
    dimensions jsonb NOT NULL,
    value numeric NOT NULL,
    unit text NOT NULL
);

CREATE INDEX IF NOT EXISTS v2_facts_lookup_idx ON v2_facts(filing_id, fiscal_year, period_type);
