"""Read typed numeric facts from an SEC inline-XBRL filing."""

import re
from datetime import date
from decimal import Decimal, InvalidOperation


def split_concept(name):
    """us-gaap:NetCashProvidedByUsedInOperatingActivities -> net cash provided by ..."""
    words = re.findall(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|\d+", name.split(":")[-1])
    return " ".join(word.lower() for word in words)


def read_meta(soup):
    values, context = {}, None
    for tag in soup.find_all("ix:nonnumeric"):
        name = tag.get("name", "")
        if name.startswith("dei:") and name not in values:
            values[name] = tag.get_text(" ", strip=True)
            if name == "dei:DocumentType":
                context = tag["contextref"]  # the report's own fiscal-year period
    return {
        "fiscal_year": int(values["dei:DocumentFiscalYearFocus"]),
        "form_type": values.get("dei:DocumentType", ""),
        "cik": values.get("dei:EntityCentralIndexKey", ""),
        "context": context,
    }


def read_contexts(soup):
    contexts = {}
    for context in soup.find_all("xbrli:context"):
        start, end, instant = (
            context.find(name) for name in ("xbrli:startdate", "xbrli:enddate", "xbrli:instant")
        )
        dimensions = {
            member["dimension"]: member.get_text(strip=True)
            for member in context.find_all(["xbrldi:explicitmember", "xbrldi:typedmember"])
        }
        contexts[context["id"]] = {
            "start": date.fromisoformat(start.get_text(strip=True)) if start else None,
            "end": date.fromisoformat((end or instant).get_text(strip=True)),
            "dimensions": dimensions,
        }
    return contexts


def read_units(soup):
    units = {}
    for unit in soup.find_all("xbrli:unit"):
        measures = unit.get_text(" ", strip=True)
        if "iso4217:USD" in measures and "shares" in measures:
            units[unit["id"]] = "USD per share"
        elif "iso4217:USD" in measures:
            units[unit["id"]] = "USD"
        elif "xbrli:shares" in measures:
            units[unit["id"]] = "shares"
        elif "xbrli:pure" in measures:
            units[unit["id"]] = "pure"
        else:
            units[unit["id"]] = measures.split(":")[-1]
    return units


def period_type(context):
    if context["start"] is None:
        return "instant"
    days = (context["end"] - context["start"]).days
    return "annual" if days > 300 else "quarter" if 80 < days < 100 else "other"


def fiscal_year(context, meta, period_end):
    return meta["fiscal_year"] - round((period_end - context["end"]).days / 365.25)


def scaled(tag, unit):
    """Return (value, unit label): money and shares in millions, percentages as printed."""
    text = tag.get_text(strip=True)
    if tag.get("format", "").endswith(("fixed-zero", "zerodash")) or text in {"—", "-", "–"}:
        number = Decimal(0)
    else:
        try:
            number = Decimal(text.replace(",", ""))
        except InvalidOperation:
            return None, None
    scale = int(tag.get("scale", "0"))
    if tag.get("sign") == "-":
        number = -number
    if unit in {"USD", "shares"}:
        return number.scaleb(scale - 6), f"{unit} millions"
    if unit == "pure" and scale == -2:
        return number, "percent"
    return number.scaleb(scale), unit


def read_facts(soup, meta, contexts, units, row_of):
    """One fact per tagged number inside a table row; row_of maps a <tr> to its row record."""
    period_end = contexts[meta["context"]]["end"]
    facts = {}
    for tag in soup.find_all("ix:nonfraction"):
        row = row_of.get(id(tag.find_parent("tr")))
        context = contexts.get(tag.get("contextref"))
        if row is None or context is None:
            continue
        value, unit = scaled(tag, units.get(tag.get("unitref"), ""))
        if value is None:
            continue
        key = (tag["name"], tag["contextref"])
        fact = {
            "concept": tag["name"],
            "row_id": row["id"],
            "row_label": row["label"],
            "statement": row["statement"],
            "period_start": context["start"],
            "period_end": context["end"],
            "period_type": period_type(context),
            "fiscal_year": fiscal_year(context, meta, period_end),
            "dimensions": context["dimensions"],
            "value": value,
            "unit": unit,
        }
        # The same fact is often repeated in MD&A and notes; cite the primary statement.
        if key not in facts or (facts[key]["statement"] in {"segment", "other"} and fact["statement"] not in {"segment", "other"}):
            facts[key] = fact
    return [{**fact, "id": f"x{index}"} for index, fact in enumerate(facts.values())]
