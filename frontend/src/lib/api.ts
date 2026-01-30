const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface RunRequest {
  ticker: string;
  period_type: "10-K" | "10-Q";
  num_periods: number;
}

export interface StepLog {
  step_name: string;
  status: string;
  started_at: string | null;
  finished_at: string | null;
  duration_ms: number | null;
  input_summary: string | null;
  output_summary: string | null;
  warnings: string[];
  errors: string[];
}

export interface RunResponse {
  run_id: string;
  status: "pending" | "running" | "completed" | "failed";
  ticker: string;
  period_type: "10-K" | "10-Q";
  num_periods: number;
  created_at: string;
  finished_at: string | null;
  steps: StepLog[];
  warnings: string[];
  artifact_path: string | null;
  company_name: string | null;
  cik: string | null;
}

export interface HistoryItem {
  run_id: string;
  ticker: string;
  period_type: "10-K" | "10-Q";
  num_periods: number;
  status: "pending" | "running" | "completed" | "failed";
  created_at: string;
  finished_at: string | null;
  company_name: string | null;
}

export async function startRun(request: RunRequest): Promise<RunResponse> {
  const res = await fetch(`${API_BASE}/api/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!res.ok) throw new Error(`Failed to start run: ${res.statusText}`);
  return res.json();
}

export async function getRun(runId: string): Promise<RunResponse> {
  const res = await fetch(`${API_BASE}/api/run/${runId}`);
  if (!res.ok) throw new Error(`Failed to get run: ${res.statusText}`);
  return res.json();
}

export async function getHistory(): Promise<HistoryItem[]> {
  const res = await fetch(`${API_BASE}/api/history`);
  if (!res.ok) throw new Error(`Failed to get history: ${res.statusText}`);
  return res.json();
}

export function getDownloadUrl(runId: string): string {
  return `${API_BASE}/api/run/${runId}/download`;
}
