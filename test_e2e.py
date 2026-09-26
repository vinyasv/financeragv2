"""One real-filings, live-services acceptance test."""

import json
import os
import re

import pytest

from v2.app import ROOT, ask, ingest, init_db


def cited(result):
    return [item for item in result["evidence"] if item["id"] in result["answer"]]


@pytest.mark.skipif(
    not (os.getenv("V2_DATABASE_URL") and os.getenv("OPENROUTER_API_KEY")),
    reason="Live end-to-end test requires V2_DATABASE_URL and OPENROUTER_API_KEY",
)
def test_filings_answers():
    init_db()
    filings = json.loads((ROOT / "v2/eval/filings.json").read_text())
    for filing in filings:
        if filing["id"] in {"nvda-fy2024", "amd-fy2024"}:
            ingest(ROOT / filing["path"], filing["id"], filing["company"], filing["url"])

    # Two companies, two statements each, chained calculations.
    result = ask(
        "Calculate NVIDIA's and AMD's FY2024 operating-cash-flow margins "
        "(operating cash flow divided by revenue), then the percentage-point gap."
    )
    answer = result["answer"]
    assert result["status"] == "complete", answer
    by_company = {
        company: " ".join(item["content"] for item in cited(result) if item["company"] == company)
        for company in ("NVIDIA", "AMD")
    }
    assert all(value in by_company["NVIDIA"] for value in ("60,922", "28,090"))
    assert all(value in by_company["AMD"] for value in ("25,785", "3,041"))
    assert "Consolidated Statements of Cash Flows" in by_company["NVIDIA"]
    assert "Consolidated Statements of Operations" in by_company["AMD"]
    assert re.search(r"46\.11\s*%", answer) and re.search(r"11\.79\s*%", answer), answer
    assert "34.31 percentage points" in answer

    # Negative values keep their sign: 28,090 + (-10,566).
    result = ask(
        "What was NVIDIA's FY2024 operating cash flow plus its net cash from investing activities?"
    )
    assert "17,524" in result["answer"], result["answer"]

    # A prior-year value is looked up by period, not picked from a row by the model.
    result = ask("What was AMD's revenue growth rate from fiscal 2023 to fiscal 2024?")
    assert re.search(r"13\.69\s*%", result["answer"]), result["answer"]

    # Segment facts come from dimensioned XBRL facts.
    result = ask("What share of NVIDIA's FY2024 revenue came from the Data Center market platform?")
    assert re.search(r"78\.01\s*%", result["answer"]), result["answer"]

    # Prose search runs per company, so a comparison cites both.
    result = ask("Compare how NVIDIA and AMD describe their reliance on TSMC in their FY2024 10-Ks.")
    assert {item["company"] for item in cited(result)} >= {"NVIDIA", "AMD"}, result["answer"]
    assert all(item["kind"] != "fact" for item in result["evidence"])

    # A calculation plus a cited qualitative explanation.
    result = ask(
        "Calculate NVIDIA's FY2024 operating cash flow margin and summarize one supply "
        "constraint discussed in its filing."
    )
    assert re.search(r"46\.11\s*%", result["answer"]), result["answer"]
    assert any(item["kind"] != "fact" for item in cited(result))

    # A follow-up lookup chosen from discovered segment rows; the answer leads with the winner.
    result = ask("Which NVIDIA market platform grew fastest in fiscal 2024, and by what percentage?")
    assert "Data Center" in result["answer"].split("\n\n")[0], result["answer"]
    assert "216.73" in result["answer"], result["answer"]

    # Missing companies are reported, not guessed.
    result = ask("What was Apple's revenue in fiscal 2023?")
    assert result["status"] == "insufficient", result["answer"]
