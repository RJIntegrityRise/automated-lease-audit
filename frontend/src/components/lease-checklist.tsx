import {
  CheckCircle2,
  CircleMinus,
  HelpCircle,
  XCircle,
} from "lucide-react";

import type {
  ChecklistItemResult,
  ChecklistStatus,
  LeaseChecklistResult,
} from "@/lib/types";

type LeaseChecklistProps = {
  checklist: LeaseChecklistResult;
  onGoToPage: (page: number) => void;
};

export function LeaseChecklist({
  checklist,
  onGoToPage,
}: LeaseChecklistProps) {
  return (
    <section className="space-y-5">
      <div>
        <h2 className="text-xl font-semibold text-slate-950 dark:text-white">
          Lease completion checklist
        </h2>

        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
          Results apply only to the current independent
          scan.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-4">
        <SummaryCard
          label="Present"
          value={checklist.present_count}
        />
        <SummaryCard
          label="Missing"
          value={checklist.missing_count}
        />
        <SummaryCard
          label="Review"
          value={checklist.review_required_count}
        />
        <SummaryCard
          label="N/A"
          value={checklist.not_applicable_count}
        />
      </div>

      <div className="space-y-4">
        {checklist.sections.map((section) => (
          <details
            key={section.section_name}
            open={
              section.missing_count > 0 ||
              section.review_required_count > 0
            }
            className="overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900"
          >
            <summary className="cursor-pointer px-5 py-4">
              <div className="inline-flex flex-wrap items-center gap-3">
                <span className="font-semibold text-slate-950 dark:text-white">
                  {section.section_name}
                </span>

                <span className="text-xs text-slate-500 dark:text-slate-400">
                  {section.present_count} present ·{" "}
                  {section.missing_count} missing ·{" "}
                  {section.review_required_count} review
                </span>
              </div>
            </summary>

            <div className="divide-y divide-slate-200 border-t border-slate-200 dark:divide-slate-800 dark:border-slate-800">
              {section.items.map((item) => (
                <ChecklistRow
                  key={item.item_code}
                  item={item}
                  onGoToPage={onGoToPage}
                />
              ))}
            </div>
          </details>
        ))}
      </div>
    </section>
  );
}

function ChecklistRow({
  item,
  onGoToPage,  
}: {
  item: ChecklistItemResult;
  onGoToPage: (page: number) => void;
}) {
  const Icon = getStatusIcon(item.status);

  return (
    <div className="flex gap-3 px-5 py-4">
      <Icon
        className={`mt-0.5 h-5 w-5 shrink-0 ${getStatusClass(
          item.status,
        )}`}
      />

      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className="font-medium text-slate-950 dark:text-white">
            {item.field_name}
          </p>

          {item.required && (
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600 dark:bg-slate-800 dark:text-slate-300">
              Required
            </span>
          )}
        </div>

        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
          {item.explanation}
        </p>

        <div className="mt-3 grid gap-3 sm:grid-cols-3">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Detected value
            </p>

            <p className="mt-1 break-words text-sm font-medium text-slate-900 dark:text-white">
              {formatDetectedValue(
                item.detected_value,
              )}
            </p>
          </div>

          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Status
            </p>

            <p className="mt-1 text-sm font-medium capitalize text-slate-900 dark:text-white">
              {item.status.replaceAll(
                "_",
                " ",
              )}
            </p>
          </div>

          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Confidence
            </p>

            <p className="mt-1 text-sm font-medium text-slate-900 dark:text-white">
              {item.confidence !== null &&
              item.confidence !== undefined
                ? `${Math.round(
                    item.confidence * 100,
                  )}%`
                : "—"}
            </p>
          </div>
        </div>

        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Page
            </p>

            <p className="mt-1 text-sm font-medium text-slate-900 dark:text-white">
              {item.page_number
                ? `Page ${item.page_number}`
                : "—"}
            </p>
          </div>

          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Required
            </p>

            <p className="mt-1 text-sm font-medium text-slate-900 dark:text-white">
              {item.required ? "Yes" : "No"}
            </p>
          </div>
        </div>
        


        {item.page_number && (
          <button
            type="button"
            onClick={() =>
                onGoToPage(item.page_number!)
            }
            className="mt-3 inline-flex items-center rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            Go to page {item.page_number}
          </button>
        )}



        {item.source_text && (
          <details className="mt-3">
            <summary className="cursor-pointer text-xs font-medium text-blue-600 dark:text-blue-400">
              Evidence
            </summary>

            <p className="mt-2 rounded-lg bg-slate-50 p-3 text-xs leading-5 text-slate-700 dark:bg-slate-950 dark:text-slate-300">
              {item.source_text}
            </p>
          </details>
        )}
      </div>
    </div>
  );
}

function SummaryCard({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <p className="text-sm text-slate-500 dark:text-slate-400">
        {label}
      </p>

      <p className="mt-1 text-2xl font-bold text-slate-950 dark:text-white">
        {value}
      </p>
    </div>
  );
}

function getStatusIcon(
  status: ChecklistStatus,
) {
  switch (status) {
    case "present":
      return CheckCircle2;
    case "missing":
      return XCircle;
    case "review_required":
      return HelpCircle;
    default:
      return CircleMinus;
  }
}

function getStatusClass(
  status: ChecklistStatus,
) {
  switch (status) {
    case "present":
      return "text-green-600 dark:text-green-400";
    case "missing":
      return "text-red-600 dark:text-red-400";
    case "review_required":
      return "text-amber-600 dark:text-amber-400";
    default:
      return "text-slate-400 dark:text-slate-500";
  }
}


function formatDetectedValue(
  value: unknown,
): string {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return "Not detected";
  }

  if (Array.isArray(value)) {
    return value.length
      ? value.join(", ")
      : "Not detected";
  }

  if (typeof value === "object") {
    return JSON.stringify(value);
  }

  return String(value);
}