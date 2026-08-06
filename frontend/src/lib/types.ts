export type LeaseUploadResponse = {
  lease_id: string;
  document_id: string;
  original_filename: string;
  storage_path: string;
  file_size_bytes: number;
  page_count: number;
  extracted_character_count: number;
  status: string;
};

export type ApiErrorResponse = {
  detail?: string;
};

export type LeaseDocumentDetail = {
  id: string;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number | null;
  page_count: number | null;
  extracted_text: string | null;
  signed_url: string;
  signed_url_expires_in: number;
};

export type LeaseDetailResponse = {
  id: string;
  internal_lease_id: string | null;
  unit_number: string | null;
  status: string;
  tenant_names: string[];
  monthly_rent: number | null;
  security_deposit: number | null;
  lease_start_date: string | null;
  lease_end_date: string | null;
  extraction_confidence: number | null;
  processing_error: string | null;
  created_at: string;
  document: LeaseDocumentDetail;
};

export type AuditFinding = {
  id: string | null;
  rule_id: string | null;
  rule_code: string;
  category: string;
  status: string;
  severity: string;
  title: string;
  explanation: string;
  field_name: string | null;
  actual_value: unknown;
  expected_value: unknown;
  page_numbers: number[];
  evidence: Record<string, unknown>;
  requires_review: boolean;
};

export type AuditSummary = {
  id: string;
  lease_id: string;
  status: string;
  score: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  informational_count: number;
  total_findings: number;
  recommendation: string;
  completed_at: string | null;
  findings: AuditFinding[];
};