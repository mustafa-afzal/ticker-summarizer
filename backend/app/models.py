from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PeriodType(str, Enum):
    ANNUAL = "10-K"
    QUARTERLY = "10-Q"


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class RunRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10)
    period_type: PeriodType = PeriodType.ANNUAL
    num_periods: int = Field(default=5, ge=1, le=20)


class StepLog(BaseModel):
    step_name: str
    status: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    duration_ms: Optional[int] = None
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class RunConfig(BaseModel):
    ticker: str
    period_type: PeriodType
    num_periods: int
    mapping_version: str


class RunResponse(BaseModel):
    run_id: str
    status: RunStatus
    ticker: str
    period_type: PeriodType
    num_periods: int
    created_at: str
    finished_at: Optional[str] = None
    steps: list[StepLog] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    artifact_path: Optional[str] = None
    company_name: Optional[str] = None
    cik: Optional[str] = None


class HistoryItem(BaseModel):
    run_id: str
    ticker: str
    period_type: PeriodType
    num_periods: int
    status: RunStatus
    created_at: str
    finished_at: Optional[str] = None
    company_name: Optional[str] = None
