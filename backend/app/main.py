"""PitchSheet Agent — FastAPI backend."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.config import MAPPING_VERSION
from app.db.database import create_run, get_history, get_run, init_db
from app.models import HistoryItem, PeriodType, RunConfig, RunRequest, RunResponse, RunStatus
from app.pipeline.engine import run_pipeline

app = FastAPI(title="PitchSheet Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://ticker-summarizer.vercel.app",
        "https://ticker-summarizer-git-main-mustafa-s-projects-fe434d18.vercel.app",
        "https://ticker-summarizer-hzuskswfk-mustafa-s-projects-fe434d18.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await init_db()


@app.post("/api/run", response_model=RunResponse)
async def start_run(request: RunRequest, background_tasks: BackgroundTasks):
    """Start a new pipeline run."""
    run_id = str(uuid.uuid4())
    config = RunConfig(
        ticker=request.ticker.upper(),
        period_type=request.period_type,
        num_periods=request.num_periods,
        mapping_version=MAPPING_VERSION,
    )

    await create_run(run_id, request.ticker, request.period_type, request.num_periods, config)

    # Run pipeline in background
    background_tasks.add_task(
        run_pipeline, run_id, request.ticker, request.period_type, request.num_periods
    )

    run = await get_run(run_id)
    return run


@app.get("/api/run/{run_id}", response_model=RunResponse)
async def get_run_status(run_id: str):
    """Get the status and logs of a pipeline run."""
    run = await get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@app.get("/api/run/{run_id}/download")
async def download_workbook(run_id: str):
    """Download the generated Excel workbook."""
    run = await get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status != RunStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Run is not completed (status: {run.status})")
    if not run.artifact_path:
        raise HTTPException(status_code=404, detail="No workbook artifact found")

    path = Path(run.artifact_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Workbook file not found on disk")

    return FileResponse(
        path=str(path),
        filename=path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.get("/api/history", response_model=list[HistoryItem])
async def list_history():
    """List previous runs."""
    return await get_history()


@app.get("/api/health")
async def health():
    return {"status": "ok"}
