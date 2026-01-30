"""Generate financial charts as PNG files using matplotlib."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


def _format_billions(val: float) -> str:
    if abs(val) >= 1e9:
        return f"${val/1e9:.1f}B"
    if abs(val) >= 1e6:
        return f"${val/1e6:.0f}M"
    return f"${val:,.0f}"


def _short_date(date_str: str) -> str:
    """Convert 2024-09-28 to FY24 or Q3'24 style."""
    parts = date_str.split("-")
    if len(parts) >= 2:
        return f"FY{parts[0][2:]}"
    return date_str


def _create_bar_chart(
    dates: list[str],
    values: list[Optional[float]],
    title: str,
    ylabel: str,
    output_path: Path,
    is_currency: bool = True,
    is_pct: bool = False,
    color: str = "#2563eb",
):
    """Create a bar chart."""
    fig, ax = plt.subplots(figsize=(10, 5))

    labels = [_short_date(d) for d in dates]
    clean_values = [v if v is not None else 0 for v in values]
    colors = [color if v >= 0 else "#dc2626" for v in clean_values]

    bars = ax.bar(labels, clean_values, color=colors, width=0.6, edgecolor="white", linewidth=0.5)

    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.3, linestyle="--")

    if is_currency:
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: _format_billions(x)))
    elif is_pct:
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x*100:.1f}%"))

    # Add value labels on bars
    for bar, val in zip(bars, values):
        if val is None:
            continue
        if is_currency:
            label = _format_billions(val)
        elif is_pct:
            label = f"{val*100:.1f}%"
        else:
            label = f"{val:,.0f}"
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + abs(bar.get_height()) * 0.02,
            label,
            ha="center", va="bottom", fontsize=8,
        )

    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _create_line_chart(
    dates: list[str],
    values: list[Optional[float]],
    title: str,
    ylabel: str,
    output_path: Path,
    is_pct: bool = False,
    color: str = "#2563eb",
):
    """Create a line chart."""
    fig, ax = plt.subplots(figsize=(10, 5))

    labels = [_short_date(d) for d in dates]

    # Filter None values for plotting
    valid_indices = [i for i, v in enumerate(values) if v is not None]
    valid_labels = [labels[i] for i in valid_indices]
    valid_values = [values[i] for i in valid_indices]

    ax.plot(valid_labels, valid_values, color=color, linewidth=2.5, marker="o", markersize=6)
    ax.fill_between(valid_labels, valid_values, alpha=0.1, color=color)

    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.3, linestyle="--")

    if is_pct:
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x*100:.1f}%"))

    for i, val in zip(valid_indices, valid_values):
        if is_pct:
            label = f"{val*100:.1f}%"
        else:
            label = f"{val:,.0f}"
        ax.text(labels[i], val, label, ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def generate_charts(
    period_dates: list[str],
    normalized: dict[str, dict[str, list]],
    metrics: dict[str, list],
    output_dir: Path,
) -> list[dict]:
    """Generate all charts and return list of chart info dicts.

    Returns list of {"name": str, "path": Path, "title": str}.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    charts = []

    income = normalized.get("Income_Statement", {})
    cashflow = normalized.get("Cash_Flow", {})

    # 1. Revenue over time
    revenue = income.get("Revenue", [])
    if any(v is not None for v in revenue):
        path = output_dir / "revenue.png"
        _create_bar_chart(
            period_dates, revenue,
            "Revenue", "USD",
            path, is_currency=True, color="#2563eb",
        )
        charts.append({"name": "revenue", "path": path, "title": "Revenue Over Time"})

    # 2. Gross Margin over time
    gross_margin = metrics.get("Gross Margin", [])
    if any(v is not None for v in gross_margin):
        path = output_dir / "gross_margin.png"
        _create_line_chart(
            period_dates, gross_margin,
            "Gross Margin", "%",
            path, is_pct=True, color="#16a34a",
        )
        charts.append({"name": "gross_margin", "path": path, "title": "Gross Margin Trend"})

    # 3. Operating Margin over time
    op_margin = metrics.get("Operating Margin", [])
    if any(v is not None for v in op_margin):
        path = output_dir / "operating_margin.png"
        _create_line_chart(
            period_dates, op_margin,
            "Operating Margin", "%",
            path, is_pct=True, color="#9333ea",
        )
        charts.append({"name": "operating_margin", "path": path, "title": "Operating Margin Trend"})

    # 4. FCF over time
    fcf = cashflow.get("Free Cash Flow", [])
    if any(v is not None for v in fcf):
        path = output_dir / "fcf.png"
        _create_bar_chart(
            period_dates, fcf,
            "Free Cash Flow", "USD",
            path, is_currency=True, color="#0891b2",
        )
        charts.append({"name": "fcf", "path": path, "title": "Free Cash Flow Over Time"})

    # 5. Shares over time
    shares = income.get("Diluted Shares Outstanding", [])
    if any(v is not None for v in shares):
        path = output_dir / "shares.png"
        _create_bar_chart(
            period_dates, shares,
            "Diluted Shares Outstanding", "Shares",
            path, is_currency=False, color="#f59e0b",
        )
        charts.append({"name": "shares", "path": path, "title": "Shares Outstanding Trend"})

    return charts
