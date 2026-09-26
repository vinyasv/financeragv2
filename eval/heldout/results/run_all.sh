#!/bin/zsh
# Frozen run commands from FREEZE.md, with v2/.venv/bin/python (deviation 3).
set -e
cd /Users/vinyas/Desktop/FinanceRAG
PY=v2/.venv/bin/python
R=v2/eval/heldout/results
Q=v2/eval/heldout/questions.jsonl
step() { echo "=== $(date '+%H:%M:%S') $*"; }
step verify; shasum -a 256 -c v2/eval/heldout/FREEZE.sha256
step ingest; $PY -m v2.eval.run ingest --arm both --manifest v2/eval/heldout/filings.json
step eval v2; $PY -m v2.eval.run eval --arm v2 --runs 3 --questions $Q --out $R/v2.json
step eval k6; $PY -m v2.eval.run eval --arm baseline --k 6 --runs 3 --questions $Q --out $R/baseline_k6.json
step eval k12; $PY -m v2.eval.run eval --arm baseline --k 12 --runs 3 --questions $Q --out $R/baseline_k12.json
for f in v2 baseline_k6 baseline_k12; do step retry $f; $PY -m v2.eval.run retry $R/$f.json; done
step judge; $PY -m v2.eval.run judge $R/v2.json $R/baseline_k6.json $R/baseline_k12.json
step report; $PY -m v2.eval.analysis report $R/v2.json $R/baseline_k6.json $R/baseline_k12.json --out $R/report.md
step audit-sample; $PY -m v2.eval.analysis audit-sample $R/v2.json $R/baseline_k6.json $R/baseline_k12.json --out v2/eval/heldout/audit.csv --key v2/eval/heldout/audit_key.json
step done
