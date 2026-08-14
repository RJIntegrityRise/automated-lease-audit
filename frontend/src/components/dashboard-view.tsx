"use client";

import {
  AlertTriangle,
  FileCheck2,
  FileText,
  LoaderCircle,
  Search,
  ShieldAlert,
} from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import type {
  DashboardSummary,
  LeaseListResponse,
} from "@/lib/types";

export function DashboardView() {
  const [summary, setSummary] =
    useState<DashboardSummary | null>(null);
  const [leases, setLeases] =
    useState<LeaseListResponse | null>(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const apiUrl =
    process.env.NEXT_PUBLIC_API_URL ??
    "http://localhost:8000";

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const query = search.trim()
        ? `?search=${encodeURIComponent(search.trim())}`
        : "";

      const [summaryResponse, leasesResponse] =
        await Promise.all([
          fetch(`${apiUrl}/api/dashboard/summary`, {
            cache: "no-store",
          }),
          fetch(`${apiUrl}/api/dashboard/leases${query}`, {
            cache: "no-store",
          }),
        ]);

      if (!summaryResponse.ok || !leasesResponse.ok) {
        throw new Error("Unable to load dashboard data.");
      }

      setSummary(
        (await summaryResponse.json()) as DashboardSummary,
      );

      setLeases(
        (await leasesResponse.json()) as LeaseListResponse,
      );
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to load dashboard.",
      );
    } finally {
      setLoading(false);
    }
  }, [apiUrl, search]);

  useEffect(() => {
  // eslint-disable-next-line react-hooks/set-state-in-effect
  void loadDashboard();
  }, [loadDashboard]);

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <LoaderCircle className="h-8 w-8 animate-spin text-blue-600 dark:text-blue-400" />
      </div>
    );
  }

  if (error || !summary || !leases) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
        {error || "Unable to load dashboard."}
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-3xl font-bold text-slate-950 dark:text-white">
          Lease audit dashboard
        </h1>

        <p className="mt-2 text-slate-600 dark:text-slate-400">
          Review leases, extraction runs and independent
          audit results.
        </p>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          icon={FileText}
          label="Total leases"
          value={summary.total_leases}
        />

        <MetricCard
          icon={FileCheck2}
          label="Completed"
          value={summary.completed_count}
        />

        <MetricCard
          icon={AlertTriangle}
          label="Needs review"
          value={summary.review_required_count}
        />

        <MetricCard
          icon={ShieldAlert}
          label="High risk"
          value={summary.high_risk_count}
        />
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <div className="flex flex-col gap-4 border-b border-slate-200 p-5 sm:flex-row sm:items-center sm:justify-between dark:border-slate-800">
          <div>
            <h2 className="font-semibold text-slate-950 dark:text-white">
              Lease history
            </h2>

            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Latest run is shown. Previous scans remain
              stored independently.
            </p>
          </div>

          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" />

            <input
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
              placeholder="Search lease, unit or tenant"
              className="w-full rounded-lg border border-slate-300 bg-white py-2.5 pl-9 pr-3 text-sm text-slate-950 outline-none focus:border-blue-500 dark:border-slate-700 dark:bg-slate-950 dark:text-white sm:w-72"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[900px] text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-950 dark:text-slate-400">
              <tr>
                <th className="px-5 py-3">Lease</th>
                <th className="px-5 py-3">Unit</th>
                <th className="px-5 py-3">Tenant</th>
                <th className="px-5 py-3">Extraction</th>
                <th className="px-5 py-3">Latest score</th>
                <th className="px-5 py-3">Recommendation</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
              {leases.items.map((lease) => (
                <tr key={lease.id}>
                  <td className="px-5 py-4">
                    <p className="font-medium text-slate-950 dark:text-white">
                      {lease.internal_lease_id ??
                        lease.original_filename ??
                        "Unnamed lease"}
                    </p>

                    <p className="mt-1 text-xs text-slate-500">
                      {lease.id}
                    </p>
                  </td>

                  <td className="px-5 py-4 text-slate-700 dark:text-slate-300">
                    {lease.unit_number ?? "—"}
                  </td>

                  <td className="px-5 py-4 text-slate-700 dark:text-slate-300">
                    {lease.tenant_names.length
                      ? lease.tenant_names.join(", ")
                      : "—"}
                  </td>

                  <td className="px-5 py-4">
                    <StatusBadge
                      status={
                        lease.latest_extraction_status ??
                        lease.status
                      }
                    />
                  </td>

                  <td className="px-5 py-4 font-semibold text-slate-950 dark:text-white">
                    {lease.latest_audit_score !== null
                      ? `${lease.latest_audit_score}/100`
                      : "—"}
                  </td>

                  <td className="px-5 py-4 text-slate-700 dark:text-slate-300">
                    {lease.latest_audit_recommendation ??
                      "Not audited"}
                  </td>

                  <td className="px-5 py-4">
                    <Link
                      href={`/leases/${lease.id}`}
                      className="font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400"
                    >
                      Open
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

type MetricCardProps = {
  icon: typeof FileText;
  label: string;
  value: number;
};

function MetricCard({
  icon: Icon,
  label,
  value,
}: MetricCardProps) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
      <Icon className="h-6 w-6 text-blue-600 dark:text-blue-400" />

      <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">
        {label}
      </p>

      <p className="mt-1 text-3xl font-bold text-slate-950 dark:text-white">
        {value}
      </p>
    </div>
  );
}

function StatusBadge({
  status,
}: {
  status: string;
}) {
  return (
    <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium capitalize text-slate-700 dark:bg-slate-800 dark:text-slate-300">
      {status}
    </span>
  );
}