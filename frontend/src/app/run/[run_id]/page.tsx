"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { getRun, getDownloadUrl, startRun, type RunResponse } from "@/lib/api";

const STEP_LABELS: Record<string, string> = {
  resolve_company: "Resolving company",
  fetch_submissions: "Fetching filings metadata",
  fetch_companyfacts: "Fetching XBRL facts",
  map_to_templates: "Mapping to financial templates",
  normalize_periods: "Normalizing periods",
  compute_metrics: "Computing key metrics",
  generate_charts: "Generating charts",
  export_xlsx: "Exporting Excel workbook",
};

const ALL_STEPS = [
  "resolve_company",
  "fetch_submissions",
  "fetch_companyfacts",
  "map_to_templates",
  "normalize_periods",
  "compute_metrics",
  "generate_charts",
  "export_xlsx",
];

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending: "bg-slate-100 text-slate-600",
    running: "bg-blue-100 text-blue-700",
    completed: "bg-green-100 text-green-700",
    failed: "bg-red-100 text-red-700",
  };
  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status] || styles.pending}`}>
      {status}
    </span>
  );
}

function StepIcon({ status }: { status: string }) {
  if (status === "completed") {
    return (
      <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center">
        <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      </div>
    );
  }
  if (status === "failed") {
    return (
      <div className="w-6 h-6 rounded-full bg-red-500 flex items-center justify-center">
        <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </div>
    );
  }
  if (status === "running") {
    return (
      <div className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center animate-pulse">
        <div className="w-2 h-2 rounded-full bg-white" />
      </div>
    );
  }
  return <div className="w-6 h-6 rounded-full bg-slate-200" />;
}

export default function RunPage() {
  const params = useParams();
  const router = useRouter();
  const runId = params.run_id as string;
  const [run, setRun] = useState<RunResponse | null>(null);
  const [error, setError] = useState("");

  const poll = useCallback(async () => {
    try {
      const data = await getRun(runId);
      setRun(data);
      return data.status === "completed" || data.status === "failed";
    } catch {
      setError("Failed to fetch run status");
      return true;
    }
  }, [runId]);

  useEffect(() => {
    let active = true;
    const loop = async () => {
      const done = await poll();
      if (!done && active) {
        setTimeout(loop, 1500);
      }
    };
    loop();
    return () => { active = false; };
  }, [poll]);

  const handleRerun = async () => {
    if (!run) return;
    try {
      const newRun = await startRun({
        ticker: run.ticker,
        period_type: run.period_type,
        num_periods: run.num_periods,
      });
      router.push(`/run/${newRun.run_id}`);
    } catch {
      setError("Failed to rerun");
    }
  };

  if (error) {
    return (
      <div className="pt-12 text-center">
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  if (!run) {
    return (
      <div className="pt-12 text-center">
        <div className="animate-pulse text-slate-400">Loading run data...</div>
      </div>
    );
  }

  const completedSteps = new Map(run.steps.map((s) => [s.step_name, s]));

  // Determine current running step based on completed steps
  let currentStepIdx = -1;
  if (run.status === "running") {
    currentStepIdx = ALL_STEPS.findIndex((s) => !completedSteps.has(s) || completedSteps.get(s)?.status !== "completed");
  }

  return (
    <div className="pt-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-2xl font-bold text-slate-900">
              {run.ticker}
            </h1>
            <StatusBadge status={run.status} />
          </div>
          {run.company_name && (
            <p className="text-slate-500">{run.company_name}</p>
          )}
          <p className="text-sm text-slate-400 mt-1">
            {run.period_type} &middot; {run.num_periods} periods
            {run.cik && <> &middot; CIK: {run.cik}</>}
          </p>
        </div>
        <div className="flex gap-3">
          {run.status === "completed" && (
            <a
              href={getDownloadUrl(run.run_id)}
              className="px-4 py-2 bg-blue-700 hover:bg-blue-800 text-white rounded-lg text-sm font-medium transition-colors"
            >
              Download .xlsx
            </a>
          )}
          <button
            onClick={handleRerun}
            className="px-4 py-2 border border-slate-300 hover:bg-slate-50 rounded-lg text-sm font-medium text-slate-600 transition-colors"
          >
            Rerun
          </button>
        </div>
      </div>

      {/* Pipeline Steps */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 mb-6">
        <h2 className="text-sm font-semibold text-slate-700 mb-4 uppercase tracking-wide">
          Pipeline Progress
        </h2>
        <div className="space-y-4">
          {ALL_STEPS.map((stepName, idx) => {
            const step = completedSteps.get(stepName);
            let status = "pending";
            if (step) {
              status = step.status;
            } else if (run.status === "running" && idx === currentStepIdx) {
              status = "running";
            }

            return (
              <div key={stepName} className="flex items-start gap-3">
                <div className="pt-0.5">
                  <StepIcon status={status} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-slate-800">
                      {STEP_LABELS[stepName] || stepName}
                    </p>
                    {step?.duration_ms != null && (
                      <span className="text-xs text-slate-400">
                        {step.duration_ms < 1000
                          ? `${step.duration_ms}ms`
                          : `${(step.duration_ms / 1000).toFixed(1)}s`}
                      </span>
                    )}
                  </div>
                  {step?.output_summary && (
                    <p className="text-xs text-slate-500 mt-0.5">{step.output_summary}</p>
                  )}
                  {step?.warnings && step.warnings.length > 0 && (
                    <div className="mt-1">
                      {step.warnings.slice(0, 3).map((w, i) => (
                        <p key={i} className="text-xs text-amber-600">{w}</p>
                      ))}
                      {step.warnings.length > 3 && (
                        <p className="text-xs text-amber-500">+{step.warnings.length - 3} more warnings</p>
                      )}
                    </div>
                  )}
                  {step?.errors && step.errors.length > 0 && (
                    <div className="mt-1">
                      {step.errors.map((e, i) => (
                        <p key={i} className="text-xs text-red-600">{e}</p>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Warnings */}
      {run.warnings.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-6">
          <h2 className="text-sm font-semibold text-amber-800 mb-3 uppercase tracking-wide">
            Warnings ({run.warnings.length})
          </h2>
          <div className="space-y-1.5 max-h-60 overflow-y-auto">
            {run.warnings.map((w, i) => (
              <p key={i} className="text-xs text-amber-700 font-mono">{w}</p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
