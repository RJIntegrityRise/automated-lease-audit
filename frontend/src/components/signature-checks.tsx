import {
  CheckCircle2,
  HelpCircle,
  XCircle,
} from "lucide-react";

import type {
  SignaturePartyCheck,
} from "@/lib/types";

type SignatureChecksProps = {
  checks: SignaturePartyCheck[];
};

export function SignatureChecks({
  checks,
}: SignatureChecksProps) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <div className="border-b border-slate-200 px-5 py-4 dark:border-slate-800">
        <h2 className="font-semibold text-slate-950 dark:text-white">
          Tenant signature checks
        </h2>

        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Each named tenant is compared with detected
          signature records.
        </p>
      </div>

      {checks.length === 0 ? (
        <div className="p-5 text-sm text-amber-700 dark:text-amber-300">
          No tenant signature comparisons were available.
        </div>
      ) : (
        <div className="divide-y divide-slate-200 dark:divide-slate-800">
          {checks.map((check, index) => {
            const StatusIcon = getStatusIcon(
              check.signature_status,
            );

            return (
              <article
                key={`${check.expected_name}-${index}`}
                className="flex items-start gap-4 p-5"
              >
                <StatusIcon
                  className={getStatusClass(
                    check.signature_status,
                  )}
                />

                <div className="min-w-0 flex-1">
                  <p className="font-medium text-slate-950 dark:text-white">
                    {check.expected_name ??
                      "Unidentified tenant"}
                  </p>

                  <div className="mt-2 space-y-1 text-sm text-slate-600 dark:text-slate-400">
                    <p>
                      Signature:{" "}
                      {formatStatus(
                        check.signature_status,
                      )}
                    </p>

                    <p>
                      Name match:{" "}
                      {formatStatus(
                        check.name_match_status,
                      )}
                    </p>

                    <p>
                      Signature date:{" "}
                      {check.signature_date ??
                        formatStatus(
                          check.signature_date_status,
                        )}
                    </p>

                    {check.page_number && (
                      <p>
                        Page: {check.page_number}
                      </p>
                    )}
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}

function getStatusIcon(
  status: SignaturePartyCheck["signature_status"],
) {
  if (status === "detected") {
    return CheckCircle2;
  }

  if (status === "not_detected") {
    return XCircle;
  }

  return HelpCircle;
}

function getStatusClass(
  status: SignaturePartyCheck["signature_status"],
) {
  if (status === "detected") {
    return "mt-0.5 h-6 w-6 shrink-0 text-green-600 dark:text-green-400";
  }

  if (status === "not_detected") {
    return "mt-0.5 h-6 w-6 shrink-0 text-red-600 dark:text-red-400";
  }

  return "mt-0.5 h-6 w-6 shrink-0 text-amber-600 dark:text-amber-400";
}

function formatStatus(status: string) {
  return status.replaceAll("_", " ");
}