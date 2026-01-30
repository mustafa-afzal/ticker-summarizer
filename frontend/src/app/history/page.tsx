"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getHistory, getDownloadUrl, type HistoryItem } from "@/lib/api";

function StatusDot({ status }: { status: string }) {
  const colors: Record<string, string> = {
    pending: "bg-slate-400",
    running: "bg-blue-500 animate-pulse",
    completed: "bg-green-500",
    failed: "bg-red-500",
  };
  return <div className={`w-2.5 h-2.5 rounded-full ${colors[status] || colors.pending}`} />;
}

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export default function HistoryPage() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getHistory()
      .then(setItems)
      .catch(() => setError("Failed to load history"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="pt-6">
      <h1 className="text-2xl font-bold text-slate-900 mb-6">Run History</h1>

      {loading && <div className="text-slate-400 animate-pulse">Loading...</div>}
      {error && <div className="text-red-600">{error}</div>}

      {!loading && items.length === 0 && (
        <div className="text-center py-16">
          <p className="text-slate-400 mb-4">No runs yet</p>
          <Link href="/" className="text-blue-600 hover:text-blue-700 text-sm font-medium">
            Generate your first model
          </Link>
        </div>
      )}

      {items.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3">Ticker</th>
                <th className="px-5 py-3">Company</th>
                <th className="px-5 py-3">Type</th>
                <th className="px-5 py-3">Periods</th>
                <th className="px-5 py-3">Created</th>
                <th className="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((item) => (
                <tr key={item.run_id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-5 py-3.5">
                    <StatusDot status={item.status} />
                  </td>
                  <td className="px-5 py-3.5 font-semibold text-slate-800">
                    <Link href={`/run/${item.run_id}`} className="hover:text-blue-700">
                      {item.ticker}
                    </Link>
                  </td>
                  <td className="px-5 py-3.5 text-slate-500">
                    {item.company_name || "—"}
                  </td>
                  <td className="px-5 py-3.5 text-slate-600">{item.period_type}</td>
                  <td className="px-5 py-3.5 text-slate-600">{item.num_periods}</td>
                  <td className="px-5 py-3.5 text-slate-400 text-xs">
                    {formatDate(item.created_at)}
                  </td>
                  <td className="px-5 py-3.5">
                    <div className="flex gap-2 justify-end">
                      <Link
                        href={`/run/${item.run_id}`}
                        className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                      >
                        View
                      </Link>
                      {item.status === "completed" && (
                        <a
                          href={getDownloadUrl(item.run_id)}
                          className="text-xs text-green-600 hover:text-green-700 font-medium"
                        >
                          Download
                        </a>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
