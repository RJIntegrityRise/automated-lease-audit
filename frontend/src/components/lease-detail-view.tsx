"use client";

import {
  AlertTriangle,
  ArrowLeft,
  FileText,
  LoaderCircle,
  RefreshCw,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { authenticatedFetch } from "@/lib/api";

import { AuditResults } from "@/components/audit-results";

import { LeaseChecklist } from "@/components/lease-checklist";

import type {
  LeaseChecklistResult,
} from "@/lib/types";

import type {
  ApiErrorResponse,
  AuditSummary,
  LeaseDetailResponse,
  DeterministicScanResponse,
} from "@/lib/types";
import { SignatureChecks } from "./signature-checks";

type LeaseDetailViewProps = {
  leaseId: string;
};

export function LeaseDetailView({
  leaseId,
}: LeaseDetailViewProps) {
  const [lease, setLease] =
    useState<LeaseDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [scanning, setScanning] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [extractionMessage, setExtractionMessage] =
    useState("");
  const [extractionError, setExtractionError] =
    useState("");


  const [
    currentExtractionRunId,
    setCurrentExtractionRunId,
  ] = useState<string | null>(null);

  const [scanResult, setScanResult] =
  useState<DeterministicScanResponse | null>(
    null,
  );

   

  const [checklist, setChecklist] =
    useState<LeaseChecklistResult | null>(
      null,
    );

  const [pdfPage, setPdfPage] =
    useState<number | null>(null);

  const [auditing, setAuditing] =
    useState(false);
 
  const [auditMessage, setAuditMessage] =
    useState("");
 
  const [audit, setAudit] =
    useState<AuditSummary | null>(null);








  

  const loadLease = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await authenticatedFetch(
        `/api/leases/${leaseId}`,
        {
          method: "GET",
          cache: "no-store",
        },
      );

      if (!response.ok) {
        let message = `Request failed with status ${response.status}.`;

        try {
          const errorResponse =
            (await response.json()) as ApiErrorResponse;

          if (errorResponse.detail) {
            message = errorResponse.detail;
          }
        } catch {
          // Use the generic status message.
        }

        throw new Error(message);
      }

      const data =
        (await response.json()) as LeaseDetailResponse;

      setLease(data);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to load the lease.",
      );
    } finally {
      setLoading(false);
    }
  }, [leaseId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadLease();
  }, [loadLease]); 



  async function runDeterministicScan() {
    setScanning(true);
    setExtractionMessage("");
    setExtractionError("");

    setChecklist(null);
    setScanResult(null);
    setAudit(null);
    setAuditMessage("");
    setCurrentExtractionRunId(null);

    try {
      const response = await authenticatedFetch(
        `/api/leases/${leaseId}/scan`,
        {
          method: "POST",
        },
      );


      const responseData =
        (await response.json()) as
          | DeterministicScanResponse
          | ApiErrorResponse;

      if (!response.ok) {
        throw new Error(
          "detail" in responseData &&
            responseData.detail
            ? responseData.detail
            : "Deterministic lease scan failed.",
        );
      }

      

      const scanData =
            responseData as DeterministicScanResponse;

      const runId = scanData.extraction_run_id;

      setCurrentExtractionRunId(runId);
      setScanResult(scanData);

      const checklistResponse = await authenticatedFetch(
        `/api/leases/${leaseId}/checklist?extraction_run_id=${encodeURIComponent(
            runId,
        )}`,
        {
            method: "GET",
            cache: "no-store",
        },
      );

      if (!checklistResponse.ok) {
        let message = "Checklist evaluation failed.";

        try {
            const checklistError =
                (await checklistResponse.json()) as ApiErrorResponse;

            if (checklistError.detail) {
                message = checklistError.detail;
            }
        } catch {
            // Use the generic checklist error.
        }

        throw new Error(message);
      }

      const checklistResult =
        (await checklistResponse.json()) as LeaseChecklistResult;

      setChecklist(checklistResult);

      setExtractionMessage(
        "Basic lease conditions and checklist scanned successfully.",
      );






    } catch (scanError) {
      setExtractionError(
        scanError instanceof Error
          ? scanError.message
          : "Deterministic lease scan failed.",
      );
    } finally {
      setScanning(false);
    }
  }

  async function runGeminiExtraction() 
  {
    setChecklist(null);
    setScanResult(null);
    setExtracting(true);
    setExtractionMessage("");
    setExtractionError("");
    setCurrentExtractionRunId(null);
    setAudit(null);
    setAuditMessage("");

    try {
      const response = await authenticatedFetch(
        `/api/leases/${leaseId}/extract`,
        {
          method: "POST",
        },
      );

      if (!response.ok) {
        let message = `Extraction failed with status ${response.status}.`;

        try {
          const errorResponse =
            (await response.json()) as ApiErrorResponse;

          if (errorResponse.detail) {
            message = errorResponse.detail;
          }
        } catch {
          // Use the generic status message.
        }

        throw new Error(message);
      }

      const extractionResult = (await response.json()) as {
        extraction_run_id: string;
      };

      setCurrentExtractionRunId(
        extractionResult.extraction_run_id,
      );

       // Remove an older audit from the screen because a new
       // extraction snapshot has now been created.

      setExtractionMessage(
        "Structured lease data extracted successfully with Gemini.",
      );

      await loadLease();
    } catch (requestError) {
      setExtractionError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to extract structured lease data.",
      );
    } finally {
      setExtracting(false);
    }
  }

  
  async function runLeaseAudit() {
  if (!currentExtractionRunId) {
    setAuditMessage(
      "Run Gemini extraction before starting an audit.",
    );
    return;
  }

  setAuditing(true);
  setAuditMessage("");

  try {
    const response = await authenticatedFetch(
      `/api/leases/${leaseId}/audit?extraction_run_id=${encodeURIComponent(
        currentExtractionRunId,
      )}`,
      {
        method: "POST",
      },
    );

    if (!response.ok) {
      let message = `Audit failed with status ${response.status}.`;

      try {
        const errorData =
          (await response.json()) as ApiErrorResponse;

        if (errorData.detail) {
          message = errorData.detail;
        }
      } catch {
        // Use the generic status message.
      }

      throw new Error(message);
    }

    const result =
        (await response.json()) as AuditSummary;

        setAudit(result);
        setAuditMessage(
            "Deterministic lease audit completed.",
        );
    } catch (auditError) {
        setAuditMessage(
            auditError instanceof Error
                ? auditError.message
                : "Lease audit failed.",
        );
    } finally {
        setAuditing(false);

    }


  }



    async function downloadPdfReport() {
      if (!currentExtractionRunId) {
        setAuditMessage(
          "Run a lease scan before downloading the report.",
        );
        return;
      }

      try {
        const response = await authenticatedFetch(
          `/api/leases/${leaseId}/report.pdf?extraction_run_id=${encodeURIComponent(
            currentExtractionRunId,
          )}`,
          {
            method: "GET",
          },
        );

        if (!response.ok) {
          let message = "Unable to generate PDF report.";

          try {
            const errorResponse =
              (await response.json()) as ApiErrorResponse;

            if (errorResponse.detail) {
              message = errorResponse.detail;
            }
          } catch {
           // Use the generic error message.
          }

          throw new Error(message);
        }

        const blob = await response.blob();
        const downloadUrl =
        window.URL.createObjectURL(blob);

        const link = document.createElement("a");

        link.href = downloadUrl;
        link.download = `lease-audit-${leaseId}.pdf`;

        document.body.appendChild(link);
        link.click();
        link.remove();

        window.URL.revokeObjectURL(downloadUrl);
      } catch (downloadError) {
        setAuditMessage(
          downloadError instanceof Error
            ? downloadError.message
            : "Unable to download PDF report.",
        );
      }
    }





  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <div className="text-center">
          <LoaderCircle className="mx-auto h-8 w-8 animate-spin text-blue-600 dark:text-blue-400" />

          <p className="mt-3 text-sm text-slate-600 dark:text-slate-400">
            Loading lease document...
          </p>
        </div>
      </div>
    );
  }

  if (error || !lease) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-6 dark:border-red-900 dark:bg-red-950">
        <div className="flex items-start gap-3">
          <AlertTriangle className="h-6 w-6 shrink-0 text-red-600 dark:text-red-400" />

          <div>
            <h2 className="font-semibold text-red-900 dark:text-red-200">
              Unable to load lease
            </h2>

            <p className="mt-1 text-sm text-red-700 dark:text-red-300">
              {error}
            </p>

            <button
              type="button"
              onClick={() => void loadLease()}
              className="mt-4 inline-flex items-center gap-2 rounded-lg bg-red-700 px-4 py-2 text-sm font-medium text-white hover:bg-red-800"
            >
              <RefreshCw className="h-4 w-4" />
              Try again
            </button>
          </div>
        </div>
      </div>
    );
  }

  const extractedText =
    lease.document.extracted_text?.trim() ||
    "No readable text was extracted from this PDF. The document may be scanned or image-based.";

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to upload
          </Link>

          <h1 className="mt-3 text-2xl font-bold text-slate-950 dark:text-white">
            Lease document
          </h1>

          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            {lease.document.original_filename}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <span className="w-fit rounded-full bg-blue-100 px-3 py-1 text-sm font-medium capitalize text-blue-800 dark:bg-blue-950 dark:text-blue-300">
            {lease.status}
          </span>

          <button
            type="button"
            onClick={() => void runDeterministicScan()}
            disabled={scanning ||extracting || auditing}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {scanning ? (
                <LoaderCircle className="h-4 w-4 animate-spin" />
            ) : (
                <ShieldAlert className="h-4 w-4" />
            )}

            {scanning
                ? "Scanning..."
                : "Scan basic lease conditions"}
          </button>



          <button
            type="button"
            onClick={() => void runGeminiExtraction()}
            disabled={extracting || scanning || auditing}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-violet-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {extracting ? (
              <LoaderCircle className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4" />
            )}

            {extracting
              ? "Extracting..."
              : "Extract with Gemini"}
          </button>

          <button
            type="button"
            onClick={() => void runLeaseAudit()}
            disabled={
              auditing ||
              extracting ||
              scanning ||
              !currentExtractionRunId
            }
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {auditing ? (
              <LoaderCircle className="h-4 w-4 animate-spin" />
            ) : (
              <ShieldAlert className="h-4 w-4" />
            )}

            {auditing ? "Auditing..." : "Run lease audit"}
          </button>


          <button
            type="button"
            onClick={() => void downloadPdfReport()}
            disabled={
              !currentExtractionRunId ||
              scanning ||
              extracting ||
              auditing
            }
            className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            <FileText className="h-4 w-4" />
            Download PDF Report
          </button>


        </div>
      </div>

      {extractionMessage ? (
        <div
          role="status"
          className="rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800 dark:border-green-900 dark:bg-green-950 dark:text-green-300"
        >
          {extractionMessage}
        </div>
      ) : null}

      {extractionError ? (
        <div
          role="alert"
          className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-300"
        >
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{extractionError}</span>
        </div>
      ) : null}


      {auditMessage && (
        <p className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
           {auditMessage}
        </p>
      )}

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetadataCard
          label="Internal lease ID"
          value={lease.internal_lease_id ?? "Not provided"}
        />

        <MetadataCard
          label="Unit"
          value={lease.unit_number ?? "Not provided"}
        />

        <MetadataCard
          label="Pages"
          value={String(
            lease.document.page_count ?? "Unknown",
          )}
        />

        <MetadataCard
          label="File size"
          value={formatFileSize(
            lease.document.file_size_bytes,
          )}
        />
      </section>

      <section className="grid min-h-[700px] gap-6 xl:grid-cols-2">
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4 dark:border-slate-800">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-blue-600 dark:text-blue-400" />

              <h2 className="font-semibold text-slate-950 dark:text-white">
                Original PDF
              </h2>
            </div>

            <a
              href={lease.document.signed_url}
              target="_blank"
              rel="noreferrer"
              className="text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400"
            >
              Open in new tab
            </a>
          </div>

          <iframe
            key={`${lease.document.signed_url}-${pdfPage ?? 1}`}
            src={
              pdfPage
                ? `${lease.document.signed_url}#page=${pdfPage}`
                : lease.document.signed_url
            }
            title={`PDF preview of ${lease.document.original_filename}`}
            className="h-[700px] w-full bg-slate-100 dark:bg-slate-950"
          />
        </div>

        <div 
          id="pdf-preview"
          className="overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900"
          >
          <div className="border-b border-slate-200 px-5 py-4 dark:border-slate-800">
            <h2 className="font-semibold text-slate-950 dark:text-white">
              Extracted text
            </h2>

            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Text extracted page by page using PyMuPDF
            </p>
          </div>

          <pre className="h-[700px] overflow-auto whitespace-pre-wrap break-words p-5 font-mono text-sm leading-6 text-slate-800 dark:text-slate-200">
            {extractedText}
          </pre>
        </div>
      </section>

      {scanResult && (
        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-3">
            <MetadataCard
              label="OCR used"
              value={
                scanResult.structured_data.ocr_used
                  ? "Yes"
                  : "No"
              }
            />

            <MetadataCard
              label="OCR pages"
              value={String(
                scanResult.structured_data.ocr_page_count,
              )}
            />

            <MetadataCard
              label="Signature image review"
              value={
                scanResult.structured_data
                  .signature_image_review_required
                  ? "Required"
                  :"Not required"
              }
            />

          </div>

          <SignatureChecks
            checks={
              scanResult.structured_data
                .tenant_signature_checks
            }
          />
        </div>
      )}

      {checklist && (
        <LeaseChecklist
            checklist={checklist}
            onGoToPage={(page) => {
              setPdfPage(page);

              document
                .getElementById("pdf-preview")
                ?.scrollIntoView({
                  behavior: "smooth",
                  block: "start",
                });
            }}
        />
      )}


 


      {audit && <AuditResults audit={audit} />}
    </div>
  );
}

type MetadataCardProps = {
  label: string;
  value: string;
};

function MetadataCard({
  label,
  value,
}: MetadataCardProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
        {label}
      </p>

      <p className="mt-2 break-words font-semibold text-slate-950 dark:text-white">
        {value}
      </p>
    </div>
  );
}

function formatFileSize(
  fileSizeBytes: number | null,
): string {
  if (fileSizeBytes === null) {
    return "Unknown";
  }

  const megabytes = fileSizeBytes / 1024 / 1024;

  if (megabytes >= 1) {
    return `${megabytes.toFixed(2)} MB`;
  }

  return `${(fileSizeBytes / 1024).toFixed(1)} KB`;
}