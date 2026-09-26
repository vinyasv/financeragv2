# Freeze record: held-out evaluation

## Frozen artefacts

`FREEZE.sha256` lists the SHA-256 of every file that determines the result:

- **System code:** `app.py`, `xbrl.py`, `reasoning.py`, `schema.sql`.
- **Baseline and scoring:** `baseline.py`, `run.py`, `analysis.py`.
- **Protocol:** `PROTOCOL.md`.
- **Questions and their adjudication log.**
- **Both filing manifests,** which in turn hold the SHA-256 of every filing.

Verify before running (from the repository root):

```bash
shasum -a 256 -c v2/eval/heldout/FREEZE.sha256
```

## Question set

- **77 questions,** 7 in each of 11 categories.
- **44 on held-out companies** (Analog Devices, Marvell, ON Semiconductor, Microchip) and **33 on development companies.**
- **Pipeline:** written blind by three agents, then verified independently by two agents that answered blind before seeing the gold (verification files are timestamped). An adjudicator then resolved every disagreement.
- **Changes:** 27 questions were changed and 0 dropped, with every change logged in `adjudication.jsonl`. The adjudicator made 14 of these changes; 14 received a uniform "USD millions" clarification; h026 is in both groups. Both verifiers agreed with every gold number before adjudication.

## Models and parameters

| Item | Value |
|---|---|
| Answer model (all arms) | `openai/gpt-6-luna`, temperature 0 |
| Embeddings (all arms) | `openai/text-embedding-3-small` |
| Judge | `google/gemini-3.8-flash`, temperature 0; judge check passed (`judge_check.txt`) |
| Arms | `v2`, `baseline_k6` (primary comparator), `baseline_k12` |
| Runs per question | 3 |
| Bootstrap | 10,000 resamples, seed 20260925 |
| Human audit | 99 claims (33 per arm), seed 20260925 |

## Run commands (execute in order; do not modify)

Run on mains power. Each long step runs under `caffeinate -i`.

```bash
shasum -a 256 -c v2/eval/heldout/FREEZE.sha256
python3 -m v2.eval.run ingest --arm both --manifest v2/eval/heldout/filings.json
caffeinate -i python3 -m v2.eval.run eval --arm v2 --runs 3 --questions v2/eval/heldout/questions.jsonl --out v2/eval/heldout/results/v2.json
caffeinate -i python3 -m v2.eval.run eval --arm baseline --k 6 --runs 3 --questions v2/eval/heldout/questions.jsonl --out v2/eval/heldout/results/baseline_k6.json
caffeinate -i python3 -m v2.eval.run eval --arm baseline --k 12 --runs 3 --questions v2/eval/heldout/questions.jsonl --out v2/eval/heldout/results/baseline_k12.json
python3 -m v2.eval.run retry v2/eval/heldout/results/v2.json
python3 -m v2.eval.run retry v2/eval/heldout/results/baseline_k6.json
python3 -m v2.eval.run retry v2/eval/heldout/results/baseline_k12.json
python3 -m v2.eval.run judge v2/eval/heldout/results/v2.json v2/eval/heldout/results/baseline_k6.json v2/eval/heldout/results/baseline_k12.json
python3 -m v2.eval.analysis report v2/eval/heldout/results/v2.json v2/eval/heldout/results/baseline_k6.json v2/eval/heldout/results/baseline_k12.json --out v2/eval/heldout/results/report.md
python3 -m v2.eval.analysis audit-sample v2/eval/heldout/results/v2.json v2/eval/heldout/results/baseline_k6.json v2/eval/heldout/results/baseline_k12.json --out v2/eval/heldout/audit.csv --key v2/eval/heldout/audit_key.json
```

After the human audit sheet is filled in:

```bash
python3 -m v2.eval.analysis audit-score v2/eval/heldout/audit.csv --key v2/eval/heldout/audit_key.json
```

Every deviation from these steps is recorded below and reported with the results.

## Deviations

1. **No written sign-off.** On 26 September 2026 the author instructed in chat that the run go ahead without signing this file. The frozen files were not changed.
2. **No public timestamp.** The freeze was not published before the run. Its only evidence is the local hashes in `FREEZE.sha256` and the file timestamps (25 September 2026, 23:54–23:56).
3. **Interpreter.** Commands ran with `v2/.venv/bin/python` in place of `python3`, because the system Python lacks the dependencies. Arguments are unchanged.
4. **Power.** The run was on battery, not mains power, under `caffeinate -i`. It completed 11:32–12:07 on 26 September 2026 with 0 crashes, 0 retries and 0 unjudged attempts.

## Sign-off

- Author: _Vinyas V_
- Date: 09/26/26
- Statement: I have reviewed `PROTOCOL.md` and the frozen artefacts. No system has been run on the held-out questions.
