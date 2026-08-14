import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Info,
  ShieldAlert,
} from "lucide-react";

import type {
  AuditFinding,
  AuditSummary,
} from "@/lib/types";

type AuditResultsProps = {
  audit: AuditSummary;
};

export function AuditResults({
  audit,
}: AuditResultsProps) {
  return (
    <section className="space-y-5">
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Audit score
          </p>

          <p className="mt-2 text-4xl font-bold text-slate-950 dark:text-white">
            {audit.score}
            <span className="text-lg text-slate-400">
              /100
            </span>
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Findings
          </p>

          <p className="mt-2 text-4xl font-bold text-slate-950 dark:text-white">
            {audit.total_findings}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Recommendation
          </p>

          <p className="mt-2 font-semibold text-slate-950 dark:text-white">
            {audit.recommendation}
          </p>
        </div>
      </div>

      {audit.findings.length === 0 ? (
        <div className="rounded-2xl border border-green-200 bg-green-50 p-6 dark:border-green-900 dark:bg-green-950">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="h-6 w-6 text-green-700 dark:text-green-400" />

            <p className="font-medium text-green-900 dark:text-green-200">
              No failed audit rules were found.
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {audit.findings.map((finding) => (
            <FindingCard
              key={finding.id ?? finding.rule_code}
              finding={finding}
            />
          ))}
        </div>
      )}
    </section>
  );
}

type FindingCardProps = {
  finding: AuditFinding;
};

function FindingCard({
  finding,
}: FindingCardProps) {
  

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-start gap-4">
        <div className="mt-0.5 shrink-0">
            {getSeverityIcon(finding.severity)}
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold text-slate-950 dark:text-white">
              {finding.title}
            </h3>

            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium uppercase tracking-wide text-slate-600 dark:bg-slate-800 dark:text-slate-300">
              {finding.severity}
            </span>

            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-300">
              {finding.rule_code}
            </span>
          </div>

          <p className="mt-2 text-sm leading-6 text-slate-700 dark:text-slate-300">
            {finding.explanation}
          </p>

          {finding.page_numbers.length > 0 && (
            <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">
              Evidence pages:{" "}
              {finding.page_numbers.join(", ")}
            </p>
          )}
        </div>
      </div>
    </article>
  );
}

function getSeverityIcon(severity: string) {
  const className = `h-6 w-6 ${getSeverityClass(severity)}`;

  switch (severity) {
    case "critical":
      return <ShieldAlert className={className} />;

    case "high":
      return <AlertTriangle className={className} />;

    case "medium":
      return <AlertCircle className={className} />;

    default:
      return <Info className={className} />;
  }
}

function getSeverityClass(severity: string) {
  switch (severity) {
    case "critical":
      return "text-red-700 dark:text-red-400";
    case "high":
      return "text-orange-600 dark:text-orange-400";
    case "medium":
      return "text-amber-600 dark:text-amber-400";
    default:
      return "text-blue-600 dark:text-blue-400";
  }
}