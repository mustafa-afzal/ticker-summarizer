"""Compute financial ratios, trends, and quality flags from normalized statements."""

from __future__ import annotations

from typing import Optional


def _safe_div(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None or b == 0:
        return None
    return a / b


def _pct_change(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    if current is None or previous is None or previous == 0:
        return None
    return (current - previous) / abs(previous)


def _cagr(start: Optional[float], end: Optional[float], years: int) -> Optional[float]:
    if start is None or end is None or start <= 0 or end <= 0 or years <= 0:
        return None
    return (end / start) ** (1.0 / years) - 1.0


def compute_metrics(
    period_dates: list[str],
    normalized: dict[str, dict[str, list]],
) -> tuple[dict[str, list], list[str]]:
    """Compute key financial metrics from normalized statements.

    Returns:
        (metrics_dict, warnings) where metrics_dict maps metric names to lists
        aligned with period_dates.
    """
    warnings = []
    metrics = {}

    income = normalized.get("Income_Statement", {})
    balance = normalized.get("Balance_Sheet", {})
    cashflow = normalized.get("Cash_Flow", {})

    revenue = income.get("Revenue", [])
    gross_profit = income.get("Gross Profit", [])
    op_income = income.get("Operating Income", [])
    net_income = income.get("Net Income", [])
    shares = income.get("Diluted Shares Outstanding", [])
    fcf = cashflow.get("Free Cash Flow", [])
    total_equity = balance.get("Total Equity", [])
    lt_debt = balance.get("Long-term Debt", [])

    n = len(period_dates)

    # Revenue Growth YoY
    rev_growth = [None] * n
    for i in range(1, n):
        rev_growth[i] = _pct_change(revenue[i], revenue[i - 1]) if i < len(revenue) and i - 1 < len(revenue) else None
    metrics["Revenue Growth YoY"] = rev_growth

    # Revenue CAGR (3Y and 5Y)
    cagr_3y = [None] * n
    cagr_5y = [None] * n
    for i in range(3, n):
        if i < len(revenue) and i - 3 < len(revenue):
            cagr_3y[i] = _cagr(revenue[i - 3], revenue[i], 3)
    for i in range(5, n):
        if i < len(revenue) and i - 5 < len(revenue):
            cagr_5y[i] = _cagr(revenue[i - 5], revenue[i], 5)
    metrics["Revenue CAGR 3Y"] = cagr_3y
    metrics["Revenue CAGR 5Y"] = cagr_5y

    # Margins
    gross_margin = [None] * n
    op_margin = [None] * n
    net_margin = [None] * n
    fcf_margin = [None] * n

    for i in range(n):
        rev = revenue[i] if i < len(revenue) else None
        gp = gross_profit[i] if i < len(gross_profit) else None
        oi = op_income[i] if i < len(op_income) else None
        ni = net_income[i] if i < len(net_income) else None
        fc = fcf[i] if i < len(fcf) else None

        gross_margin[i] = _safe_div(gp, rev)
        op_margin[i] = _safe_div(oi, rev)
        net_margin[i] = _safe_div(ni, rev)
        fcf_margin[i] = _safe_div(fc, rev)

    metrics["Gross Margin"] = gross_margin
    metrics["Operating Margin"] = op_margin
    metrics["Net Margin"] = net_margin
    metrics["FCF Margin"] = fcf_margin

    # Debt / Equity
    debt_equity = [None] * n
    for i in range(n):
        debt = lt_debt[i] if i < len(lt_debt) else None
        equity = total_equity[i] if i < len(total_equity) else None
        debt_equity[i] = _safe_div(debt, equity)
    metrics["Debt / Equity"] = debt_equity

    # Shares trend (pct change YoY)
    shares_change = [None] * n
    for i in range(1, n):
        s_cur = shares[i] if i < len(shares) else None
        s_prev = shares[i - 1] if i - 1 < len(shares) else None
        shares_change[i] = _pct_change(s_cur, s_prev)
    metrics["Shares Change YoY"] = shares_change

    # Quality flags: large one-time jumps in revenue or net income
    quality_flags = [None] * n
    for i in range(1, n):
        flags = []
        rev_chg = _pct_change(
            revenue[i] if i < len(revenue) else None,
            revenue[i - 1] if i - 1 < len(revenue) else None,
        )
        ni_chg = _pct_change(
            net_income[i] if i < len(net_income) else None,
            net_income[i - 1] if i - 1 < len(net_income) else None,
        )
        if rev_chg is not None and abs(rev_chg) > 0.5:
            flags.append(f"Revenue {'jumped' if rev_chg > 0 else 'dropped'} {abs(rev_chg)*100:.0f}%")
        if ni_chg is not None and abs(ni_chg) > 1.0:
            flags.append(f"Net Income {'jumped' if ni_chg > 0 else 'dropped'} {abs(ni_chg)*100:.0f}%")
        quality_flags[i] = "; ".join(flags) if flags else None
    metrics["Quality Flags"] = quality_flags

    return metrics, warnings
