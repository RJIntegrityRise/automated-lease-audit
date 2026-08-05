"use client";

import {
  CheckCircle2,
  FileText,
  LoaderCircle,
  UploadCloud,
  XCircle,
} from "lucide-react";
import { ChangeEvent, FormEvent, useRef, useState } from "react";

import type {
  ApiErrorResponse,
  LeaseUploadResponse,
} from "@/lib/types";

const MAX_FILE_SIZE_BYTES = 32 * 1024 * 1024;

type UploadState = "idle" | "uploading" | "success" | "error";

export function LeaseUploadForm() {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [unitNumber, setUnitNumber] = useState("");
  const [internalLeaseId, setInternalLeaseId] = useState("");
  const [uploadState, setUploadState] =
    useState<UploadState>("idle");
  const [message, setMessage] = useState("");
  const [result, setResult] =
    useState<LeaseUploadResponse | null>(null);

  const apiUrl =
    process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  function resetStatus() {
    setUploadState("idle");
    setMessage("");
    setResult(null);
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    resetStatus();

    const selectedFile = event.target.files?.[0] ?? null;

    if (!selectedFile) {
      setFile(null);
      return;
    }

    if (selectedFile.type !== "application/pdf") {
      setFile(null);
      setUploadState("error");
      setMessage("Only PDF files are supported.");
      event.target.value = "";
      return;
    }

    if (selectedFile.size > MAX_FILE_SIZE_BYTES) {
      setFile(null);
      setUploadState("error");
      setMessage("The selected PDF exceeds the 32 MB limit.");
      event.target.value = "";
      return;
    }

    setFile(selectedFile);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!file) {
      setUploadState("error");
      setMessage("Select a PDF before uploading.");
      return;
    }

    const formData = new FormData();

    formData.append("file", file);

    if (unitNumber.trim()) {
      formData.append("unit_number", unitNumber.trim());
    }

    if (internalLeaseId.trim()) {
      formData.append(
        "internal_lease_id",
        internalLeaseId.trim(),
      );
    }

    setUploadState("uploading");
    setMessage("Uploading and extracting lease text...");
    setResult(null);

    try {
      const response = await fetch(
        `${apiUrl}/api/leases/upload`,
        {
          method: "POST",
          body: formData,
        },
      );

      if (!response.ok) {
        let errorMessage = `Upload failed with status ${response.status}.`;

        try {
          const errorData =
            (await response.json()) as ApiErrorResponse;

          if (errorData.detail) {
            errorMessage = errorData.detail;
          }
        } catch {
          // Keep the generic HTTP error message.
        }

        throw new Error(errorMessage);
      }

      const uploadResult =
        (await response.json()) as LeaseUploadResponse;

      setResult(uploadResult);
      setUploadState("success");
      setMessage("Lease uploaded and processed successfully.");
    } catch (error) {
      setUploadState("error");
      setMessage(
        error instanceof Error
          ? error.message
          : "An unexpected upload error occurred.",
      );
    }
  }

  function clearForm() {
    setFile(null);
    setUnitNumber("");
    setInternalLeaseId("");
    setUploadState("idle");
    setMessage("");
    setResult(null);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  return (
    <div className="rounded-2xl border border-border bg-card text-card-foreground shadow-sm">
      <div className="border-b border-border px-6 py-5">
        <h2 className="text-xl font-semibold text-card-foreground">
          Upload lease
        </h2>

        <p className="mt-1 text-sm text-muted-foreground">
          Upload a digital residential lease PDF for text
          extraction.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="space-y-6 p-6"
      >
        <div>
          <label
            htmlFor="lease-file"
            className="mb-2 block text-sm font-medium text-slate-800 dark:text-slate-200"
          >
            Lease PDF
          </label>

          <label
            htmlFor="lease-file"
            className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-border bg-muted/40 px-6 py-10 text-center transition hover:border-primary hover:bg-muted/70"
          >
            <UploadCloud className="mb-3 h-10 w-10 text-primary" />

            <span className="font-medium text-foreground">
              Choose a PDF document
            </span>

            <span className="mt-1 text-sm text-muted-foreground">
              PDF only, maximum 32 MB
            </span>

            <input
              ref={fileInputRef}
              id="lease-file"
              name="lease-file"
              type="file"
              accept="application/pdf,.pdf"
              onChange={handleFileChange}
              disabled={uploadState === "uploading"}
              className="sr-only"
            />
          </label>

          {file && (
            <div className="mt-3 flex items-center gap-3 rounded-lg border border-border bg-muted/50 px-4 py-3">
              <FileText className="h-5 w-5 shrink-0 text-primary" />

              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-foreground">
                  {file.name}
                </p>

                <p className="text-xs text-muted-foreground">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
          )}
        </div>

        <div className="grid gap-5 sm:grid-cols-2">
          <div>
            <label
              htmlFor="unit-number"
              className="mb-2 block text-sm font-medium text-foreground"
            >
              Unit number
            </label>

            <input
              id="unit-number"
              type="text"
              value={unitNumber}
              onChange={(event) =>
                setUnitNumber(event.target.value)
              }
              disabled={uploadState === "uploading"}
              placeholder="Example: 101"
              className="w-full rounded-lg border border-input bg-background px-3 py-2.5 text-foreground outline-none transition placeholder:text-muted-foreground focus:border-primary focus:ring-2 focus:ring-primary/20 disabled:cursor-not-allowed disabled:opacity-60"
            />
          </div>

          <div>
            <label
              htmlFor="internal-lease-id"
              className="mb-2 block text-sm font-medium text-slate-800 dark:text-slate-200"
            >
              Internal lease ID
            </label>

            <input
              id="internal-lease-id"
              type="text"
              value={internalLeaseId}
              onChange={(event) =>
                setInternalLeaseId(event.target.value)
              }
              disabled={uploadState === "uploading"}
              placeholder="Example: TEST-LEASE-001"
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
            />
          </div>
        </div>

        {message && (
          <div
            className={`flex items-start gap-3 rounded-lg border px-4 py-3 text-sm ${
              uploadState === "success"
                ? "border-green-200 bg-green-50 text-green-800 dark:border-green-900 dark:bg-green-950 dark:text-green-300"
                : uploadState === "error"
                  ? "border-red-200 bg-red-50 text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-300"
                  : "border-blue-200 bg-blue-50 text-blue-800 dark:border-blue-900 dark:bg-blue-950 dark:text-blue-300"
            }`}
          >
            {uploadState === "uploading" && (
              <LoaderCircle className="h-5 w-5 shrink-0 animate-spin" />
            )}

            {uploadState === "success" && (
              <CheckCircle2 className="h-5 w-5 shrink-0" />
            )}

            {uploadState === "error" && (
              <XCircle className="h-5 w-5 shrink-0" />
            )}

            <span>{message}</span>
          </div>
        )}

        {result && (
          <div className="rounded-xl border border-border bg-muted/40 p-4">
            <h3 className="font-semibold text-foreground">
              Processing result
            </h3>

            <dl className="mt-4 grid gap-4 text-sm sm:grid-cols-2">
              <ResultItem
                label="File"
                value={result.original_filename}
              />
              <ResultItem
                label="Pages"
                value={String(result.page_count)}
              />
              <ResultItem
                label="Characters extracted"
                value={result.extracted_character_count.toLocaleString()}
              />
              <ResultItem
                label="Status"
                value={result.status}
              />
              <ResultItem
                label="Lease ID"
                value={result.lease_id}
              />
              <ResultItem
                label="Document ID"
                value={result.document_id}
              />
            </dl>
          </div>
        )}

        <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <button
            type="button"
            onClick={clearForm}
            disabled={uploadState === "uploading"}
            className="rounded-lg border border-border bg-card px-5 py-2.5 font-medium text-card-foreground transition hover:bg-muted disabled:cursor-not-allowed disabled:opacity-60"
          >
            Clear
          </button>

          <button
            type="submit"
            disabled={!file || uploadState === "uploading"}
            className="flex items-center justify-center gap-2 rounded-lg bg-primary px-5 py-2.5 font-medium text-primary-foreground transition hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:ring-offset-2 focus:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50"
          >
            {uploadState === "uploading" ? (
              <>
                <LoaderCircle className="h-5 w-5 animate-spin" />
                Processing
              </>
            ) : (
              <>
                <UploadCloud className="h-5 w-5" />
                Upload lease
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

type ResultItemProps = {
  label: string;
  value: string;
};

function ResultItem({ label, value }: ResultItemProps) {
  return (
    <div className="min-w-0">
      <dt className="text-muted-foreground">
        {label}
      </dt>

      <dd className="mt-1 break-all font-medium text-foreground">
        {value}
      </dd>
    </div>
  );
}