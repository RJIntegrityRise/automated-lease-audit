export type SignaturePartyCheck = {
  role: "tenant" | "landlord" | "unknown";
  expected_name: string | null;
  detected_name: string | null;
  name_match_status:
    | "detected"
    | "not_detected"
    | "unknown";
  signature_status:
    | "detected"
    | "not_detected"
    | "unknown";
  signature_date: string | null;
  signature_date_status:
    | "detected"
    | "not_detected"
    | "unknown";
  page_number: number | null;
  source_text: string | null;
  detection_method: string;
};



export type DeterministicScanResponse = {
  extraction_run_id: string;
  lease_id: string;
  document_id: string;
  status: string;
  structured_data: {
    tenant_names: string[];
    tenant_signature_checks: SignaturePartyCheck[];
    unmatched_tenant_names: string[];
    unmatched_signature_names: string[];
    
    ocr_used: boolean;
    ocr_page_count: number;
    signature_image_review_required: boolean;

  };
};



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

export type DashboardSummary = {
  total_leases: number;
  uploaded_count: number;
  extracting_count: number;
  completed_count: number;
  failed_count: number;
  total_audits: number;
  review_required_count: number;
  high_risk_count: number;
  average_score: number | null;
};

export type LeaseListItem = {
  id: string;
  internal_lease_id: string | null;
  unit_number: string | null;
  tenant_names: string[];
  status: string;
  created_at: string;
  updated_at: string;

  original_filename: string | null;
  page_count: number | null;

  latest_extraction_run_id: string | null;
  latest_extraction_status: string | null;
  latest_extraction_created_at: string | null;

  latest_audit_id: string | null;
  latest_audit_score: number | null;
  latest_audit_recommendation: string | null;
  latest_audit_created_at: string | null;
};

export type LeaseListResponse = {
  items: LeaseListItem[];
  total: number;
};

export type ChecklistStatus =
  | "present"
  | "missing"
  | "review_required"
  | "not_applicable";

export type ChecklistItemResult = {
  item_code: string;
  section_name: string;
  field_name: string;
  description: string | null;
  status: ChecklistStatus;
  severity: string;
  required: boolean;
  detected_value: unknown;
  page_number: number | null;
  source_text: string | null;
  confidence: number | null;
  explanation: string;
};

export type ChecklistSectionResult = {
  section_name: string;
  total_items: number;
  present_count: number;
  missing_count: number;
  review_required_count: number;
  not_applicable_count: number;
  items: ChecklistItemResult[];
};

export type LeaseChecklistResult = {
  extraction_run_id: string;
  total_items: number;
  present_count: number;
  missing_count: number;
  review_required_count: number;
  not_applicable_count: number;
  sections: ChecklistSectionResult[];
};