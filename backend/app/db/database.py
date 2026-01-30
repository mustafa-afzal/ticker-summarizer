import json
import aiosqlite
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from app.config import DB_PATH
from app.models import RunStatus, PeriodType, StepLog, RunResponse, HistoryItem, RunConfig

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    ticker TEXT NOT NULL,
    cik TEXT,
    company_name TEXT,
    period_type TEXT NOT NULL,
    num_periods INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    config_json TEXT,
    created_at TEXT NOT NULL,
    finished_at TEXT,
    artifact_path TEXT,
    warnings_json TEXT DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS step_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    step_name TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    duration_ms INTEGER,
    input_summary TEXT,
    output_summary TEXT,
    warnings_json TEXT DEFAULT '[]',
    errors_json TEXT DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_step_logs_run_id ON step_logs(run_id);
CREATE INDEX IF NOT EXISTS idx_runs_created ON runs(created_at DESC);
"""


async def init_db():
    async with aiosqlite.connect(str(DB_PATH)) as db:
        await db.executescript(DB_SCHEMA)
        await db.commit()


async def create_run(run_id: str, ticker: str, period_type: PeriodType,
                     num_periods: int, config: RunConfig) -> None:
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(str(DB_PATH)) as db:
        await db.execute(
            """INSERT INTO runs (run_id, ticker, period_type, num_periods, status, config_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (run_id, ticker.upper(), period_type.value, num_periods,
             RunStatus.PENDING.value, config.model_dump_json(), now)
        )
        await db.commit()


async def update_run_status(run_id: str, status: RunStatus,
                            cik: str = None, company_name: str = None,
                            artifact_path: str = None, warnings: list[str] = None):
    async with aiosqlite.connect(str(DB_PATH)) as db:
        fields = ["status = ?"]
        values = [status.value]

        if status in (RunStatus.COMPLETED, RunStatus.FAILED):
            fields.append("finished_at = ?")
            values.append(datetime.now(timezone.utc).isoformat())

        if cik is not None:
            fields.append("cik = ?")
            values.append(cik)
        if company_name is not None:
            fields.append("company_name = ?")
            values.append(company_name)
        if artifact_path is not None:
            fields.append("artifact_path = ?")
            values.append(artifact_path)
        if warnings is not None:
            fields.append("warnings_json = ?")
            values.append(json.dumps(warnings))

        values.append(run_id)
        await db.execute(
            f"UPDATE runs SET {', '.join(fields)} WHERE run_id = ?",
            values
        )
        await db.commit()


async def insert_step_log(run_id: str, step: StepLog):
    async with aiosqlite.connect(str(DB_PATH)) as db:
        await db.execute(
            """INSERT INTO step_logs
               (run_id, step_name, status, started_at, finished_at, duration_ms,
                input_summary, output_summary, warnings_json, errors_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (run_id, step.step_name, step.status, step.started_at, step.finished_at,
             step.duration_ms, step.input_summary, step.output_summary,
             json.dumps(step.warnings), json.dumps(step.errors))
        )
        await db.commit()


async def get_run(run_id: str) -> Optional[RunResponse]:
    async with aiosqlite.connect(str(DB_PATH)) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,))
        row = await cursor.fetchone()
        if not row:
            return None

        step_cursor = await db.execute(
            "SELECT * FROM step_logs WHERE run_id = ? ORDER BY id", (run_id,)
        )
        step_rows = await step_cursor.fetchall()

        steps = [
            StepLog(
                step_name=s["step_name"],
                status=s["status"],
                started_at=s["started_at"],
                finished_at=s["finished_at"],
                duration_ms=s["duration_ms"],
                input_summary=s["input_summary"],
                output_summary=s["output_summary"],
                warnings=json.loads(s["warnings_json"] or "[]"),
                errors=json.loads(s["errors_json"] or "[]"),
            )
            for s in step_rows
        ]

        return RunResponse(
            run_id=row["run_id"],
            status=RunStatus(row["status"]),
            ticker=row["ticker"],
            period_type=PeriodType(row["period_type"]),
            num_periods=row["num_periods"],
            created_at=row["created_at"],
            finished_at=row["finished_at"],
            steps=steps,
            warnings=json.loads(row["warnings_json"] or "[]"),
            artifact_path=row["artifact_path"],
            company_name=row["company_name"],
            cik=row["cik"],
        )


async def get_history() -> list[HistoryItem]:
    async with aiosqlite.connect(str(DB_PATH)) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM runs ORDER BY created_at DESC LIMIT 100"
        )
        rows = await cursor.fetchall()
        return [
            HistoryItem(
                run_id=r["run_id"],
                ticker=r["ticker"],
                period_type=PeriodType(r["period_type"]),
                num_periods=r["num_periods"],
                status=RunStatus(r["status"]),
                created_at=r["created_at"],
                finished_at=r["finished_at"],
                company_name=r["company_name"],
            )
            for r in rows
        ]
