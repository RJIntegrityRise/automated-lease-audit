"use client";

import {
  AlertTriangle,
  ArrowLeft,
  FileText,
  LoaderCircle,
  RefreshCw,
} from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import type {
  ApiErrorResponse,
  LeaseDetailResponse,
} from "@/lib/types";

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

  const apiUrl =
    process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  const loadLease = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${apiUrl}/api/leases/${leaseId}`,
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
  }, [apiUrl, leaseId]);

  useEffect(() => {
    void loadLease();
  }, [loadLease]);

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

        <span className="w-fit rounded-full bg-blue-100 px-3 py-1 text-sm font-medium capitalize text-blue-800 dark:bg-blue-950 dark:text-blue-300">
          {lease.status}
        </span>
      </div>

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
          value={String(lease.document.page_count ?? "Unknown")}
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
            src={lease.document.signed_url}
            title={`PDF preview of ${lease.document.original_filename}`}
            className="h-[700px] w-full bg-slate-100 dark:bg-slate-950"
          />
        </div>

        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
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