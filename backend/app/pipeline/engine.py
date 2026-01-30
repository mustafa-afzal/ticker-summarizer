"""Deterministic workflow engine that executes the PitchSheet pipeline.

Steps:
1. resolve_company(ticker) -> cik
2. fetch_submissions(cik) -> filings metadata
3. fetch_companyfacts(cik) -> XBRL facts JSON
4. map_to_templates(facts, period_type) -> standardized statements
5. normalize_periods(statements) -> aligned periods & consistent units
6. compute_metrics(statements) -> ratios + trends
7. generate_charts(metrics) -> chart images
8. export_xlsx(statements, metrics, charts) -> workbook
"""

from __future__ import annotations

import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

from app.config import ARTIFACTS_DIR, MAPPING_VERSION, SEC_BASE_URL
from app.db.database import insert_step_log, update_run_status
from app.models import PeriodType, RunConfig, RunStatus, StepLog
from app.sec.client import fetch_company_facts, fetch_submissions, resolve_cik
from app.mapping.mapper import map_facts_to_statements, normalize_periods
from app.mapping.metrics import compute_metrics
from app.charts.generator import generate_charts
from app.export.workbook import export_workbook


async def _log_step(run_id: str, step_name: str, status: str,
                    started: float, input_summary: str = None,
                    output_summary: str = None,
                    warnings: list[str] = None, errors: list[str] = None):
    finished = time.time()
    step = StepLog(
        step_name=step_name,
        status=status,
        started_at=datetime.fromtimestamp(started, tz=timezone.utc).isoformat(),
        finished_at=datetime.fromtimestamp(finished, tz=timezone.utc).isoformat(),
        duration_ms=int((finished - started) * 1000),
        input_summary=input_summary,
        output_summary=output_summary,
        warnings=warnings or [],
        errors=errors or [],
    )
    await insert_step_log(run_id, step)


async def run_pipeline(run_id: str, ticker: str, period_type: PeriodType, num_periods: int):
    """Execute the full pipeline. Updates DB throughout."""
    all_warnings = []
    data_urls = []

    await update_run_status(run_id, RunStatus.RUNNING)

    run_dir = ARTIFACTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    charts_dir = run_dir / "charts"

    try:
        # Step 1: Resolve company
        t0 = time.time()
        try:
            company_info = await resolve_cik(ticker)
            cik = company_info["cik_str"]
            company_name = company_info["title"]
            await update_run_status(run_id, RunStatus.RUNNING,
                                    cik=cik, company_name=company_name)
            await _log_step(run_id, "resolve_company", "completed", t0,
                            input_summary=f"ticker={ticker}",
                            output_summary=f"cik={cik}, name={company_name}")
        except Exception as e:
            await _log_step(run_id, "resolve_company", "failed", t0,
                            input_summary=f"ticker={ticker}",
                            errors=[str(e)])
            raise

        # Step 2: Fetch submissions
        t0 = time.time()
        try:
            submissions = await fetch_submissions(cik)
            url = f"{SEC_BASE_URL}/submissions/CIK{cik}.json"
            data_urls.append(url)
            recent_filings = submissions.get("filings", {}).get("recent", {})
            n_filings = len(recent_filings.get("accessionNumber", []))
            await _log_step(run_id, "fetch_submissions", "completed", t0,
                            input_summary=f"cik={cik}",
                            output_summary=f"{n_filings} recent filings found")
        except Exception as e:
            await _log_step(run_id, "fetch_submissions", "failed", t0,
                            errors=[str(e)])
            raise

        # Step 3: Fetch company facts
        t0 = time.time()
        try:
            company_facts = await fetch_company_facts(cik)
            url = f"{SEC_BASE_URL}/api/xbrl/companyfacts/CIK{cik}.json"
            data_urls.append(url)
            us_gaap_tags = list(company_facts.get("facts", {}).get("us-gaap", {}).keys())
            await _log_step(run_id, "fetch_companyfacts", "completed", t0,
                            input_summary=f"cik={cik}",
                            output_summary=f"{len(us_gaap_tags)} US-GAAP tags available")
        except Exception as e:
            await _log_step(run_id, "fetch_companyfacts", "failed", t0,
                            errors=[str(e)])
            raise

        # Step 4: Map to templates
        t0 = time.time()
        try:
            statements, map_warnings = map_facts_to_statements(
                company_facts, period_type, num_periods
            )
            all_warnings.extend(map_warnings)
            total_items = sum(len(v) for v in statements.values())
            filled = sum(
                1 for sheet in statements.values()
                for items in sheet.values() if items
            )
            await _log_step(run_id, "map_to_templates", "completed", t0,
                            input_summary=f"period_type={period_type.value}, num_periods={num_periods}",
                            output_summary=f"{filled}/{total_items} line items populated",
                            warnings=map_warnings)
        except Exception as e:
            await _log_step(run_id, "map_to_templates", "failed", t0,
                            errors=[str(e)])
            raise

        # Step 5: Normalize periods
        t0 = time.time()
        try:
            period_dates, normalized = normalize_periods(statements, num_periods)
            await _log_step(run_id, "normalize_periods", "completed", t0,
                            input_summary=f"num_periods={num_periods}",
                            output_summary=f"{len(period_dates)} aligned periods: {period_dates[0] if period_dates else 'N/A'} to {period_dates[-1] if period_dates else 'N/A'}")
        except Exception as e:
            await _log_step(run_id, "normalize_periods", "failed", t0,
                            errors=[str(e)])
            raise

        # Step 6: Compute metrics
        t0 = time.time()
        try:
            metrics, metric_warnings = compute_metrics(period_dates, normalized)
            all_warnings.extend(metric_warnings)
            await _log_step(run_id, "compute_metrics", "completed", t0,
                            input_summary=f"{len(period_dates)} periods",
                            output_summary=f"{len(metrics)} metrics computed",
                            warnings=metric_warnings)
        except Exception as e:
            await _log_step(run_id, "compute_metrics", "failed", t0,
                            errors=[str(e)])
            raise

        # Step 7: Generate charts
        t0 = time.time()
        try:
            charts = generate_charts(period_dates, normalized, metrics, charts_dir)
            await _log_step(run_id, "generate_charts", "completed", t0,
                            input_summary=f"{len(period_dates)} periods",
                            output_summary=f"{len(charts)} charts generated")
        except Exception as e:
            await _log_step(run_id, "generate_charts", "failed", t0,
                            errors=[str(e)])
            # Non-fatal: continue without charts
            charts = []
            all_warnings.append(f"Chart generation failed: {e}")

        # Step 8: Export workbook
        t0 = time.time()
        try:
            run_config = RunConfig(
                ticker=ticker.upper(),
                period_type=period_type,
                num_periods=num_periods,
                mapping_version=MAPPING_VERSION,
            )
            workbook_path = export_workbook(
                ticker=ticker.upper(),
                period_type=period_type.value,
                period_dates=period_dates,
                normalized=normalized,
                metrics=metrics,
                charts=charts,
                run_config=run_config.model_dump(),
                warnings=all_warnings,
                data_urls=data_urls,
                output_dir=run_dir,
            )
            await _log_step(run_id, "export_xlsx", "completed", t0,
                            input_summary=f"ticker={ticker.upper()}",
                            output_summary=f"workbook saved to {workbook_path.name}")
        except Exception as e:
            await _log_step(run_id, "export_xlsx", "failed", t0,
                            errors=[str(e)])
            raise

        # Mark run as completed
        await update_run_status(
            run_id, RunStatus.COMPLETED,
            artifact_path=str(workbook_path),
            warnings=all_warnings,
        )

    except Exception as e:
        await update_run_status(
            run_id, RunStatus.FAILED,
            warnings=all_warnings + [f"Pipeline failed: {str(e)}"],
        )
        raise
