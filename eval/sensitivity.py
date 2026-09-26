"""Post-hoc sensitivity check for required-figure coverage (not pre-registered).

The frozen metric counts a gold figure as found if any number in the answer is within
tolerance, whatever label it is attached to. The strict variant also requires the judge to
have marked that figure's claim ("<note>: <value>") as stated, i.e. tied to the right metric,
company and period. The judge already graded these claims during the frozen run; `score()`
simply ignored its verdicts on them. No model is called here.

    python -m v2.eval.sensitivity <v2.json> <baseline_k6.json> <baseline_k12.json> --out sensitivity.md
"""

import argparse
from pathlib import Path

from v2.eval.analysis import bootstrap_ci, holm, load, sign_test
from v2.eval.run import numbers

ARMS = ("v2", "baseline_k6", "baseline_k12")


def figures(question, attempt):
    """(loose, strict) per gold figure; None for attempts that are not scored numerically."""
    gold = question.get("gold", [])
    if not gold or attempt["error"] or not attempt.get("judge"):
        return None
    found = numbers(attempt["answer"])
    stated = attempt["judge"]["stated"][: len(gold)]  # numeric claims come first (run.claims)
    loose = [any(abs(n - float(g["value"])) <= float(g.get("tolerance") or 0) + 1e-9 for n in found) for g in gold]
    return loose, [m and s for m, s in zip(loose, stated)]


def per_question(data, which, keep=lambda q: True):
    runs = {}
    for attempt in data["attempts"]:
        question = data["questions"][attempt["id"]]
        pair = figures(question, attempt) if keep(question) else None
        if pair:
            matched = pair[which]
            runs.setdefault(attempt["id"], []).append(sum(matched) / len(matched))
    return {qid: sum(v) / len(v) for qid, v in runs.items()}


def compare(a, b, which):
    qa, qb = per_question(a, which), per_question(b, which)
    common = sorted(set(qa) & set(qb))
    diffs = [qa[q] - qb[q] for q in common]
    low, high = bootstrap_ci(diffs)
    p, wins, losses = sign_test(diffs)
    mean = lambda values: sum(values) / len(values)
    return len(common), mean([qa[q] for q in common]), mean([qb[q] for q in common]), mean(diffs), low, high, wins, losses, p


def pooled(data, which):
    flags = [f for a in data["attempts"] if (pair := figures(data["questions"][a["id"]], a)) for f in pair[which]]
    return sum(flags) / len(flags)


def report(paths, out):
    arms = dict(zip(ARMS, map(load, paths)))
    v2 = arms["v2"]
    tests = {f"{label}, v2 vs {arm}": compare(v2, arms[arm], which)
             for arm in ARMS[1:] for which, label in ((0, "loose (frozen)"), (1, "strict"))}
    adjusted = holm({name: t[-1] for name, t in tests.items()})
    lines = [
        "# Sensitivity: required figures bound to their label (post-hoc)",
        "",
        "Loose is the frozen metric (`run.score()[\"numeric\"]`). Strict also requires the judge's verdict on that",
        "figure's claim to be \"stated\". Strict therefore depends on the LLM judge, which the human audit has not",
        "validated. Unit: question, mean over runs, questions with gold figures only.",
        "",
        "| comparison | questions | v2 | comparator | difference [95% bootstrap CI] | wins/losses | p (sign test) | p (Holm) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name, (n, a, b, d, low, high, wins, losses, p) in tests.items():
        lines.append(f"| {name} | {n} | {a:.1%} | {b:.1%} | {d:+.1%} [{low:+.1%}, {high:+.1%}] "
                     f"| {wins}/{losses} | {p:.2g} | {adjusted[name]:.2g} |")

    lines += ["", "## By slice (question-level mean, loose → strict)", "",
              "| slice | " + " | ".join(ARMS) + " |", "|---" * (len(ARMS) + 1) + "|"]
    slices = [("all", lambda q: True)]
    slices += [(f"portion: {p}", lambda q, p=p: q.get("portion") == p) for p in ("heldout", "development")]
    slices += [(c, lambda q, c=c: q["category"] == c) for c in sorted({q["category"] for q in v2["questions"].values()})]
    for name, keep in slices:
        cells = []
        for data in arms.values():
            loose, strict = per_question(data, 0, keep), per_question(data, 1, keep)
            cells.append(f"{sum(loose.values()) / len(loose):.0%} → {sum(strict.values()) / len(strict):.0%}" if loose else "-")
        lines.append(f"| {name} | " + " | ".join(cells) + " |")

    lines += ["", "Pooled over all gold figures and attempts (loose → strict): "
              + ", ".join(f"{arm} {pooled(d, 0):.1%} → {pooled(d, 1):.1%}" for arm, d in arms.items())]

    lines += ["", "## Figures matched by number but not stated by the judge", "",
              "| arm | question | run | figure | judge quote |", "|---|---|---|---|---|"]
    for arm, data in arms.items():
        for attempt in data["attempts"]:
            question = data["questions"][attempt["id"]]
            pair = figures(question, attempt)
            if not pair:
                continue
            for i, (loose, strict) in enumerate(zip(*pair)):
                if loose and not strict:
                    gold = question["gold"][i]
                    quote = attempt["judge"]["quotes"][i].replace("|", "/").replace("\n", " ")[:120]
                    lines.append(f"| {arm} | {attempt['id']} | {attempt['run']} | {gold['note']}: {gold['value']} | {quote or '(none)'} |")
    text = "\n".join(lines) + "\n"
    Path(out).write_text(text)
    print(text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("results", nargs=3, help="v2, baseline_k6 and baseline_k12 results files")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    report(args.results, args.out)


if __name__ == "__main__":
    main()
