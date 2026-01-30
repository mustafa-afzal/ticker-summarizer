"""Maps SEC XBRL company facts to standardized financial statement templates."""

from __future__ import annotations

import re
from typing import Optional

from app.mapping.templates import ALL_TEMPLATES
from app.models import PeriodType


def _get_facts_for_tag(company_facts: dict, tag: str) -> Optional[dict]:
    """Look up a tag in the us-gaap taxonomy."""
    us_gaap = company_facts.get("facts", {}).get("us-gaap", {})
    return us_gaap.get(tag)


def _extract_periods(
    fact_data: dict,
    unit_key: str,
    period_type: PeriodType,
    num_periods: int,
) -> list[dict]:
    """Extract period values from XBRL fact data.

    For income/cash flow (duration items on 10-K): look for entries with
    'start' and 'end' where the duration is ~12 months for annual, ~3 months for quarterly.

    For balance sheet (instant items): look for entries with 'end' only.

    Returns list of {period_end, value, form} sorted by period_end descending.
    """
    units_data = fact_data.get("units", {})

    # Determine the correct unit key
    actual_unit_key = None
    if unit_key == "USD" and "USD" in units_data:
        actual_unit_key = "USD"
    elif unit_key == "shares" and "shares" in units_data:
        actual_unit_key = "shares"
    elif unit_key == "USD/shares" and "USD/shares" in units_data:
        actual_unit_key = "USD/shares"
    elif unit_key == "USD" and "USD" not in units_data:
        # Sometimes tagged differently
        for k in units_data:
            if "USD" in k.upper():
                actual_unit_key = k
                break
    elif unit_key == "shares" and "shares" not in units_data:
        for k in units_data:
            if "share" in k.lower():
                actual_unit_key = k
                break

    if actual_unit_key is None:
        return []

    entries = units_data[actual_unit_key]

    target_form = "10-K" if period_type == PeriodType.ANNUAL else "10-Q"

    results = []
    seen_periods = set()

    for entry in entries:
        form = entry.get("form", "")
        # Accept the target form or the annual report for balance sheet items
        if form != target_form and not (target_form == "10-Q" and form == "10-K"):
            # For quarterly, also accept 10-Q
            if form != target_form:
                continue

        val = entry.get("val")
        if val is None:
            continue

        period_end = entry.get("end")
        if not period_end:
            continue

        # For duration items (income statement, cash flow), check the period length
        period_start = entry.get("start")
        if period_start:
            # Duration-based item
            if period_type == PeriodType.ANNUAL:
                # ~12 months: 350-380 days
                from datetime import datetime
                try:
                    start_dt = datetime.strptime(period_start, "%Y-%m-%d")
                    end_dt = datetime.strptime(period_end, "%Y-%m-%d")
                    days = (end_dt - start_dt).days
                    if days < 350 or days > 380:
                        continue
                except ValueError:
                    continue
            else:
                # Quarterly: ~80-100 days
                from datetime import datetime
                try:
                    start_dt = datetime.strptime(period_start, "%Y-%m-%d")
                    end_dt = datetime.strptime(period_end, "%Y-%m-%d")
                    days = (end_dt - start_dt).days
                    if days < 80 or days > 100:
                        continue
                except ValueError:
                    continue

        # Deduplicate by period_end (take the latest filing)
        if period_end not in seen_periods:
            seen_periods.add(period_end)
            results.append({
                "period_end": period_end,
                "value": val,
                "form": form,
            })
        else:
            # Update with the latest value (entries are chronological)
            for r in results:
                if r["period_end"] == period_end:
                    r["value"] = val
                    break

    # Sort by period_end descending and take the most recent N
    results.sort(key=lambda x: x["period_end"], reverse=True)
    return results[:num_periods]


def map_facts_to_statements(
    company_facts: dict,
    period_type: PeriodType,
    num_periods: int,
) -> tuple[dict[str, dict[str, list[dict]]], list[str]]:
    """Map XBRL company facts to standardized statement templates.

    Returns:
        (statements, warnings) where statements is:
        {
            "Income_Statement": {
                "Revenue": [{"period_end": "2024-09-28", "value": 123456}, ...],
                ...
            },
            ...
        }
    """
    statements = {}
    warnings = []

    for sheet_name, template in ALL_TEMPLATES.items():
        sheet_data = {}

        for line_item, config in template.items():
            if config.get("computed"):
                sheet_data[line_item] = []  # Will be computed later
                continue

            tags = config["tags"]
            unit_key = config["units"]

            # Try all tags and pick the one with the most recent data
            best_periods = []
            best_max_date = ""
            for tag in tags:
                fact_data = _get_facts_for_tag(company_facts, tag)
                if fact_data is None:
                    continue

                periods = _extract_periods(fact_data, unit_key, period_type, num_periods)
                if periods:
                    max_date = max(p["period_end"] for p in periods)
                    if max_date > best_max_date or (max_date == best_max_date and len(periods) > len(best_periods)):
                        best_periods = periods
                        best_max_date = max_date

            found = bool(best_periods)
            if found:
                sheet_data[line_item] = best_periods

            if not found:
                sheet_data[line_item] = []
                warnings.append(
                    f"{sheet_name}.{line_item}: no data found "
                    f"(tried tags: {', '.join(tags[:3])}{'...' if len(tags) > 3 else ''})"
                )

        statements[sheet_name] = sheet_data

    # Compute derived fields
    _compute_derived(statements, warnings)

    return statements, warnings


def _compute_derived(statements: dict, warnings: list[str]):
    """Compute derived line items like Free Cash Flow."""
    cf = statements.get("Cash_Flow", {})
    cfo = cf.get("Net Cash from Operations", [])
    capex = cf.get("Capital Expenditures", [])

    if cfo and capex:
        # Build a lookup by period_end for capex
        capex_by_period = {p["period_end"]: p["value"] for p in capex}

        fcf = []
        for period in cfo:
            pe = period["period_end"]
            cfo_val = period["value"]
            capex_val = capex_by_period.get(pe, 0)
            # Capex is typically reported as positive in XBRL but is a cash outflow
            # FCF = CFO - |Capex|
            fcf.append({
                "period_end": pe,
                "value": cfo_val - abs(capex_val),
                "form": period.get("form", ""),
            })
        cf["Free Cash Flow"] = fcf
    else:
        if not cfo:
            warnings.append("Cash_Flow.Free Cash Flow: cannot compute, no CFO data")
        if not capex:
            warnings.append("Cash_Flow.Free Cash Flow: cannot compute, no Capex data")


def normalize_periods(
    statements: dict[str, dict[str, list[dict]]],
    num_periods: int,
) -> tuple[list[str], dict[str, dict[str, list]]]:
    """Align all statements to a common set of period-end dates.

    Returns:
        (period_dates, normalized_statements) where:
        - period_dates is a sorted list of period-end date strings
        - normalized_statements has values as simple lists aligned to period_dates
    """
    # Collect all unique period-end dates
    all_dates = set()
    for sheet_data in statements.values():
        for line_item_data in sheet_data.values():
            for entry in line_item_data:
                all_dates.add(entry["period_end"])

    # Sort chronologically and take the most recent N
    sorted_dates = sorted(all_dates, reverse=True)[:num_periods]
    sorted_dates.reverse()  # Now oldest first

    # Normalize each statement to these dates
    normalized = {}
    for sheet_name, sheet_data in statements.items():
        norm_sheet = {}
        for line_item, entries in sheet_data.items():
            val_by_date = {e["period_end"]: e["value"] for e in entries}
            norm_sheet[line_item] = [val_by_date.get(d) for d in sorted_dates]
        normalized[sheet_name] = norm_sheet

    return sorted_dates, normalized
