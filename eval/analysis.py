"""Pre-registered analysis for the held-out evaluation (heldout/PROTOCOL.md, sections 9 and 10).

    python -m v2.eval.analysis report <v2.json> <baseline_k6.json> <baseline_k12.json>
    python -m v2.eval.analysis audit-sample <results.json ...> --out audit.csv --key audit_key.json
    python -m v2.eval.analysis audit-score audit.csv --key audit_key.json
    python -m v2.eval.analysis judge-check
"""

import argparse
import csv
import json
import math
import random
from pathlib import Path

from v2.eval.run import JUDGE_MODEL, judge_attempt, score

SEED = 20260925
RESAMPLES = 10_000
HERE = Path(__file__).resolve().parent
# Fixed planted-error cases on development answers: (question, run, [(original text, planted error)]).
PLANTED = [
    ("p02", 1, [("February 14", "March 3"), ("May 26", "July 9")]),
    ("p18", 1, [("Micron’s SBU had the highest", "Micron’s MBU had the highest")]),
    ("p05", 1, [("Intel’s modem assets", "Broadcom’s modem assets")]),
    ("p03", 1, [("by 2025", "by 2027")]),
    ("p16", 2, [("Data Center grew fastest", "Gaming grew fastest")]),
]


def load(path):
    return json.loads(Path(path).read_text())


def per_question(data, metric):
    """Each question's mean of `metric` over its runs; questions without the metric are left out."""
    runs = {}
    for attempt in data["attempts"]:
        value = score(data["questions"][attempt["id"]], attempt)[metric]
        if value is not None:
            runs.setdefault(attempt["id"], []).append(float(value))
    return {qid: sum(values) / len(values) for qid, values in runs.items()}


def bootstrap_ci(diffs):
    rng = random.Random(SEED)
    means = sorted(sum(rng.choices(diffs, k=len(diffs))) / len(diffs) for _ in range(RESAMPLES))
    return means[int(0.025 * RESAMPLES)], means[int(0.975 * RESAMPLES) - 1]


def sign_test(diffs):
    """Exact two-sided sign test; ties are dropped."""
    wins, losses = sum(d > 0 for d in diffs), sum(d < 0 for d in diffs)
    n = wins + losses
    if n == 0:
        return 1.0, wins, losses
    tail = sum(math.comb(n, i) for i in range(min(wins, losses) + 1)) / 2**n
    return min(1.0, 2 * tail), wins, losses


def holm(pvalues):
    """Holm–Bonferroni adjusted p-values, keyed like the input."""
    ordered = sorted(pvalues, key=pvalues.get)
    adjusted, running = {}, 0.0
    for rank, key in enumerate(ordered):
        running = max(running, min(1.0, (len(ordered) - rank) * pvalues[key]))
        adjusted[key] = running
    return adjusted


def wilson(successes, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan")
    p = successes / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - half, centre + half


def compare(a, b, metric):
    """Paired comparison of two arms on per-question means of `metric` (a minus b)."""
    qa, qb = per_question(a, metric), per_question(b, metric)
    common = sorted(set(qa) & set(qb))
    diffs = [qa[q] - qb[q] for q in common]
    low, high = bootstrap_ci(diffs)
    p, wins, losses = sign_test(diffs)
    return {
        "n": len(common),
        "a": sum(qa[q] for q in common) / len(common),
        "b": sum(qb[q] for q in common) / len(common),
        "diff": sum(diffs) / len(diffs),
        "ci": (low, high),
        "p": p,
        "wins": wins,
        "losses": losses,
    }


def attempt_rate(data, keep=lambda question: True):
    rows = [
        score(data["questions"][a["id"]], a)["correct"]
        for a in data["attempts"]
        if keep(data["questions"][a["id"]])
    ]
    k, n = sum(rows), len(rows)
    low, high = wilson(k, n)
    return f"{k / n:.0%} [{low:.0%}, {high:.0%}] (n={n})" if n else "-"


def agreement(data):
    runs = {}
    for attempt in data["attempts"]:
        runs.setdefault(attempt["id"], set()).add(score(data["questions"][attempt["id"]], attempt)["correct"])
    return sum(len(v) == 1 for v in runs.values()) / len(runs)


def report(v2_path, k6_path, k12_path):
    v2, k6, k12 = load(v2_path), load(k6_path), load(k12_path)
    tests = {
        "H1 correct, v2 vs baseline_k6 (primary)": compare(v2, k6, "correct"),
        "H2 correct, v2 vs baseline_k12": compare(v2, k12, "correct"),
        "H3 numeric accuracy, v2 vs baseline_k6": compare(v2, k6, "numeric"),
        "H4 citation support, v2 vs baseline_k6": compare(v2, k6, "citation_support"),
    }
    adjusted = holm({name: t["p"] for name, t in tests.items() if not name.startswith("H1")})
    lines = [
        "## Hypothesis tests (unit: question; per-question mean over runs)",
        "",
        "| test | questions | v2 | comparator | difference [95% bootstrap CI] | wins/losses | p (sign test) | p (Holm) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name, t in tests.items():
        holm_p = "—" if name.startswith("H1") else f"{adjusted[name]:.2g}"
        lines.append(
            f"| {name} | {t['n']} | {t['a']:.1%} | {t['b']:.1%} | {t['diff']:+.1%} "
            f"[{t['ci'][0]:+.1%}, {t['ci'][1]:+.1%}] | {t['wins']}/{t['losses']} | {t['p']:.2g} | {holm_p} |"
        )
    arms = {"v2": v2, "baseline_k6": k6, "baseline_k12": k12}
    lines += ["", "## Correct answers, attempt level [95% Wilson interval]", "",
              "| slice | " + " | ".join(arms) + " |", "|---" * (len(arms) + 1) + "|"]
    slices = [("all", lambda q: True)]
    slices += [(f"portion: {p}", lambda q, p=p: q.get("portion") == p) for p in ("heldout", "development")]
    categories = sorted({q["category"] for q in v2["questions"].values()})
    slices += [(c, lambda q, c=c: q["category"] == c) for c in categories]
    for name, keep in slices:
        lines.append(f"| {name} | " + " | ".join(attempt_rate(d, keep) for d in arms.values()) + " |")
    lines += ["", "Run-to-run agreement: " + ", ".join(f"{a} {agreement(d):.0%}" for a, d in arms.items())]
    print("\n".join(lines))
    return "\n".join(lines)


def audit_sample(paths, out, key_path, n=100):
    """A blinded, arm-stratified random sample of judged claims for human labelling."""
    rng = random.Random(SEED)
    pools = []
    for path in paths:
        data = load(path)
        pool = [
            (data["arm"], attempt, i)
            for attempt in data["attempts"]
            if attempt.get("judge")
            for i in range(len(attempt["judge"]["claims"]))
        ]
        pools.append(rng.sample(pool, min(len(pool), n // len(paths))))
    rows = [row for pool in pools for row in pool]
    rng.shuffle(rows)
    key = []
    with open(out, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["row", "question", "claim", "answer", "cited evidence", "human_stated (y/n)", "human_supported (y/n)"])
        for row_id, (arm, attempt, i) in enumerate(rows, 1):
            data_question = attempt["id"]
            cited = [e for e in attempt["evidence"] if e["id"] in attempt["cited_ids"]]
            evidence = "\n\n".join(f"[{e['id']}] {e['content']}" for e in cited)[:6000]
            writer.writerow([row_id, data_question, attempt["judge"]["claims"][i], attempt["answer"], evidence, "", ""])
            key.append({"row": row_id, "arm": arm, "id": attempt["id"], "run": attempt["run"], "claim": i,
                        "judge_stated": attempt["judge"]["stated"][i], "judge_supported": attempt["judge"]["supported"][i]})
    Path(key_path).write_text(json.dumps(key, indent=2) + "\n")
    print(f"wrote {len(rows)} blinded rows to {out}; key in {key_path}")


def judge_check(repeats=2):
    """Protocol 9.1: the judge must fail every planted claim and pass every unedited answer."""
    from v2.app import OpenRouter

    data = load(HERE / "results" / "2026-09-25_v2_constrained.json")
    passed = True
    with OpenRouter() as router:
        for qid, run, edits in PLANTED:
            question = data["questions"][qid]
            original = next(a for a in data["attempts"] if a["id"] == qid and a["run"] == run)
            planted = original["answer"]
            for old, new in edits:
                assert old in planted, f"{qid}: planted text not found"
                planted = planted.replace(old, new)
            clean = judge_attempt(router, question, original)["stated"]
            bad = [judge_attempt(router, question, {**original, "answer": planted})["stated"] for _ in range(repeats)]
            ok = all(clean) and all(not all(verdict) for verdict in bad)
            passed &= ok
            print(f"{qid}: original {clean}; planted {bad}; {'PASS' if ok else 'FAIL'}")
    print(f"judge {JUDGE_MODEL}: {'PASS' if passed else 'FAIL'}")
    return passed


def kappa(pairs):
    n = len(pairs)
    observed = sum(a == b for a, b in pairs) / n
    p_a, p_b = sum(a for a, _ in pairs) / n, sum(b for _, b in pairs) / n
    expected = p_a * p_b + (1 - p_a) * (1 - p_b)
    return observed, (observed - expected) / (1 - expected) if expected < 1 else float("nan")


def audit_score(csv_path, key_path):
    key = {row["row"]: row for row in json.loads(Path(key_path).read_text())}
    stated, supported = [], []
    with open(csv_path, newline="") as handle:
        for row in csv.DictReader(handle):
            truth = key[int(row["row"])]
            human_stated = row["human_stated (y/n)"].strip().lower()
            human_supported = row["human_supported (y/n)"].strip().lower()
            if human_stated in {"y", "n"}:
                stated.append((human_stated == "y", truth["judge_stated"]))
            if human_supported in {"y", "n"}:
                supported.append((human_supported == "y", truth["judge_supported"]))
    for name, pairs in (("stated", stated), ("supported", supported)):
        if pairs:
            observed, k = kappa(pairs)
            print(f"{name}: n={len(pairs)} agreement={observed:.1%} Cohen's kappa={k:.2f}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    report_parser = commands.add_parser("report")
    report_parser.add_argument("v2")
    report_parser.add_argument("baseline_k6")
    report_parser.add_argument("baseline_k12")
    report_parser.add_argument("--out")
    sample_parser = commands.add_parser("audit-sample")
    sample_parser.add_argument("results", nargs="+")
    sample_parser.add_argument("--out", required=True)
    sample_parser.add_argument("--key", required=True)
    sample_parser.add_argument("--n", type=int, default=99, help="split equally across the result files")
    commands.add_parser("judge-check")
    score_parser = commands.add_parser("audit-score")
    score_parser.add_argument("csv")
    score_parser.add_argument("--key", required=True)
    args = parser.parse_args()
    if args.command == "report":
        text = report(args.v2, args.baseline_k6, args.baseline_k12)
        if args.out:
            Path(args.out).write_text(text + "\n")
    elif args.command == "audit-sample":
        audit_sample(args.results, args.out, args.key, args.n)
    elif args.command == "judge-check":
        judge_check()
    else:
        audit_score(args.csv, args.key)


if __name__ == "__main__":
    main()
