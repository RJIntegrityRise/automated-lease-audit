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