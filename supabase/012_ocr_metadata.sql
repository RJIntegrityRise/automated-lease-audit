alter table public.lease_documents
add column if not exists ocr_metadata jsonb
not null default '{}'::jsonb;

alter table public.lease_documents
add column if not exists ocr_used boolean
not null default false;

alter table public.lease_documents
add column if not exists ocr_page_count integer
not null default 0;