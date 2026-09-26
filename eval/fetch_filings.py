"""Download the evaluation corpus of 10-K HTML filings from SEC EDGAR."""

import hashlib
import json
import os
import sys
import time
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
COMPANIES = {
    "nvda": ("NVIDIA", 1045810),
    "amd": ("AMD", 2488),
    "intc": ("Intel", 50863),
    "qcom": ("Qualcomm", 804328),
    "avgo": ("Broadcom", 1730168),
    "mu": ("Micron", 723125),
    "txn": ("Texas Instruments", 97476),
}
# Held-out companies: never used while developing v2; used only for the confirmatory evaluation.
HELDOUT = {
    "adi": ("Analog Devices", 6281),
    "mrvl": ("Marvell", 1835632),
    "on": ("ON Semiconductor", 1097864),
    "mchp": ("Microchip", 827054),
}
YEARS = (2022, 2023, 2024)


def main():
    heldout = "--heldout" in sys.argv
    companies, manifest_path = (HELDOUT, HERE / "heldout" / "filings.json") if heldout else (COMPANIES, HERE / "filings.json")
    agent = os.getenv("SEC_USER_AGENT", "FinanceRAG research contact@example.com")
    client = httpx.Client(headers={"User-Agent": agent}, timeout=60, follow_redirects=True)
    (HERE / "sources").mkdir(exist_ok=True)
    manifest = []
    for ticker, (company, cik) in companies.items():
        recent = client.get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json").json()
        recent = recent["filings"]["recent"]
        for i, form in enumerate(recent["form"]):
            if form != "10-K" or int(recent["reportDate"][i][:4] or 0) not in YEARS:
                continue
            year = int(recent["reportDate"][i][:4])
            accession = recent["accessionNumber"][i].replace("-", "")
            document = recent["primaryDocument"][i]
            url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{document}"
            path = HERE / "sources" / document
            if not path.exists():
                time.sleep(0.2)
                response = client.get(url)
                response.raise_for_status()
                path.write_bytes(response.content)
            manifest.append(
                {
                    "id": f"{ticker}-fy{year}",
                    "company": company,
                    "fiscal_year": year,
                    "url": url,
                    "path": str(path.relative_to(HERE.parents[1])),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
            print(manifest[-1]["id"], document)
    manifest_path.parent.mkdir(exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
