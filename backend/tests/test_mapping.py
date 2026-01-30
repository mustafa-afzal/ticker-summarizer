"""Tests for tag mapping and period normalization."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.mapping.mapper import map_facts_to_statements, normalize_periods
from app.mapping.metrics import compute_metrics
from app.models import PeriodType


def test_map_annual_revenue(aapl_company_facts):
    """Test that annual revenue is correctly extracted."""
    statements, warnings = map_facts_to_statements(
        aapl_company_facts, PeriodType.ANNUAL, 5
    )
    revenue = statements["Income_Statement"]["Revenue"]
    assert len(revenue) == 5
    # Most recent first
    assert revenue[0]["period_end"] == "2024-09-28"
    assert revenue[0]["value"] == 391035000000


def test_map_all_income_statement_items(aapl_company_facts):
    """Test that key income statement items are populated."""
    statements, _ = map_facts_to_statements(
        aapl_company_facts, PeriodType.ANNUAL, 5
    )
    income = statements["Income_Statement"]
    assert len(income["Revenue"]) == 5
    assert len(income["Gross Profit"]) == 5
    assert len(income["Operating Income"]) == 5
    assert len(income["Net Income"]) == 5
    assert len(income["Diluted Shares Outstanding"]) == 5
    assert len(income["Diluted EPS"]) == 5


def test_map_balance_sheet(aapl_company_facts):
    """Test balance sheet mapping (instant items, no start date)."""
    statements, _ = map_facts_to_statements(
        aapl_company_facts, PeriodType.ANNUAL, 5
    )
    balance = statements["Balance_Sheet"]
    assert len(balance["Total Assets"]) == 5
    assert len(balance["Total Equity"]) == 5


def test_map_cash_flow_and_fcf(aapl_company_facts):
    """Test cash flow mapping and FCF computation."""
    statements, _ = map_facts_to_statements(
        aapl_company_facts, PeriodType.ANNUAL, 5
    )
    cf = statements["Cash_Flow"]
    assert len(cf["Net Cash from Operations"]) == 5
    assert len(cf["Capital Expenditures"]) == 5
    assert len(cf["Free Cash Flow"]) == 5

    # FCF = CFO - |Capex|
    # FY2024: 118254B - 9959B = 108295B
    fcf_2024 = cf["Free Cash Flow"][0]
    assert fcf_2024["value"] == 118254000000 - 9959000000


def test_missing_tag_produces_warning(aapl_company_facts):
    """Test that missing tags produce warnings."""
    statements, warnings = map_facts_to_statements(
        aapl_company_facts, PeriodType.ANNUAL, 5
    )
    # R&D and SGA are not in our fixture, so they should produce warnings
    warning_items = [w for w in warnings if "Research & Development" in w or "Selling, General" in w]
    assert len(warning_items) >= 2


def test_normalize_periods(aapl_company_facts):
    """Test period normalization aligns all statements."""
    statements, _ = map_facts_to_statements(
        aapl_company_facts, PeriodType.ANNUAL, 5
    )
    period_dates, normalized = normalize_periods(statements, 5)

    assert len(period_dates) == 5
    # Dates should be sorted chronologically (oldest first)
    assert period_dates[0] < period_dates[-1]

    # All line items should have exactly len(period_dates) values
    for sheet_data in normalized.values():
        for line_item, values in sheet_data.items():
            assert len(values) == len(period_dates), f"{line_item} has wrong number of values"


def test_fewer_periods(aapl_company_facts):
    """Test requesting fewer periods than available."""
    statements, _ = map_facts_to_statements(
        aapl_company_facts, PeriodType.ANNUAL, 3
    )
    period_dates, normalized = normalize_periods(statements, 3)
    assert len(period_dates) <= 3


def test_compute_metrics(aapl_company_facts, sample_period_dates):
    """Test metrics computation."""
    statements, _ = map_facts_to_statements(
        aapl_company_facts, PeriodType.ANNUAL, 5
    )
    period_dates, normalized = normalize_periods(statements, 5)
    metrics, warnings = compute_metrics(period_dates, normalized)

    assert "Revenue Growth YoY" in metrics
    assert "Gross Margin" in metrics
    assert "Operating Margin" in metrics
    assert "Net Margin" in metrics
    assert "FCF Margin" in metrics
    assert "Debt / Equity" in metrics

    # Verify gross margin calculation for most recent period
    gross_margin = metrics["Gross Margin"]
    # Find the index for the latest period
    latest_idx = len(period_dates) - 1
    if gross_margin[latest_idx] is not None:
        # AAPL FY2024: 180683B / 391035B ≈ 46.2%
        assert 0.40 < gross_margin[latest_idx] < 0.50


def test_metrics_revenue_growth(aapl_company_facts):
    """Test revenue growth calculation."""
    statements, _ = map_facts_to_statements(
        aapl_company_facts, PeriodType.ANNUAL, 5
    )
    period_dates, normalized = normalize_periods(statements, 5)
    metrics, _ = compute_metrics(period_dates, normalized)

    rev_growth = metrics["Revenue Growth YoY"]
    # First period should be None (no prior period)
    assert rev_growth[0] is None
    # FY2020->FY2021: (365817 - 274515) / 274515 ≈ 33.3%
    assert rev_growth[1] is not None
    assert 0.30 < rev_growth[1] < 0.36


def test_metrics_schema(aapl_company_facts):
    """Regression test: metrics output has expected keys."""
    statements, _ = map_facts_to_statements(
        aapl_company_facts, PeriodType.ANNUAL, 5
    )
    period_dates, normalized = normalize_periods(statements, 5)
    metrics, _ = compute_metrics(period_dates, normalized)

    expected_keys = {
        "Revenue Growth YoY",
        "Revenue CAGR 3Y",
        "Revenue CAGR 5Y",
        "Gross Margin",
        "Operating Margin",
        "Net Margin",
        "FCF Margin",
        "Debt / Equity",
        "Shares Change YoY",
        "Quality Flags",
    }
    assert set(metrics.keys()) == expected_keys
