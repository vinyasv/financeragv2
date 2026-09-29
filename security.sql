-- Supabase exposes the public schema through its REST API with a public anon key.
-- RLS with no policies blocks that API; the app connects as the table owner, which bypasses RLS.
-- Run after `init --reset` or a baseline ingest (schema.sql is frozen, so this lives here).
ALTER TABLE IF EXISTS v2_filings ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS v2_passages ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS v2_table_rows ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS v2_facts ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS v2_baseline_chunks ENABLE ROW LEVEL SECURITY;
