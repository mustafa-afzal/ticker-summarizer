"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { startRun } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [ticker, setTicker] = useState("");
  const [periodType, setPeriodType] = useState<"10-K" | "10-Q">("10-K");
  const [numPeriods, setNumPeriods] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticker.trim()) {
      setError("Please enter a ticker symbol");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const run = await startRun({
        ticker: ticker.trim().toUpperCase(),
        period_type: periodType,
        num_periods: numPeriods,
      });
      router.push(`/run/${run.run_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to start run");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center pt-12">
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold text-slate-900 mb-3">
          Generate a Pitch-Ready Excel Model
        </h1>
        <p className="text-slate-500 max-w-lg mx-auto">
          Enter a ticker symbol to pull SEC filings and generate a standardized
          financial model with statements, ratios, and charts.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md bg-white rounded-xl border border-slate-200 shadow-sm p-8"
      >
        <div className="mb-5">
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            Ticker Symbol
          </label>
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            placeholder="e.g. AAPL"
            className="w-full px-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder:text-slate-400"
          />
        </div>

        <div className="mb-5">
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            Filing Type
          </label>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => {
                setPeriodType("10-K");
                setNumPeriods(5);
              }}
              className={`flex-1 py-2.5 rounded-lg text-sm font-medium border transition-colors ${
                periodType === "10-K"
                  ? "bg-blue-50 border-blue-300 text-blue-700"
                  : "bg-white border-slate-300 text-slate-600 hover:bg-slate-50"
              }`}
            >
              Annual (10-K)
            </button>
            <button
              type="button"
              onClick={() => {
                setPeriodType("10-Q");
                setNumPeriods(12);
              }}
              className={`flex-1 py-2.5 rounded-lg text-sm font-medium border transition-colors ${
                periodType === "10-Q"
                  ? "bg-blue-50 border-blue-300 text-blue-700"
                  : "bg-white border-slate-300 text-slate-600 hover:bg-slate-50"
              }`}
            >
              Quarterly (10-Q)
            </button>
          </div>
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            Number of Periods
          </label>
          <input
            type="number"
            value={numPeriods}
            onChange={(e) => setNumPeriods(parseInt(e.target.value) || 1)}
            min={1}
            max={20}
            className="w-full px-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <p className="text-xs text-slate-400 mt-1">
            {periodType === "10-K" ? "years" : "quarters"} of data to include
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 bg-blue-700 hover:bg-blue-800 disabled:bg-blue-400 text-white rounded-lg text-sm font-semibold transition-colors"
        >
          {loading ? "Starting..." : "Generate Model"}
        </button>
      </form>
    </div>
  );
}
