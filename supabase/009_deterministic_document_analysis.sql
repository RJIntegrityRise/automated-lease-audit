alter table public.lease_documents
add column if not exists document_metadata jsonb not null default '{}'::jsonb;

alter table public.extraction_runs
add column if not exists extraction_method text not null default 'ai';

alter table public.extraction_runs
add column if not exists scanner_version text;

create index if not exists extraction_runs_method_idx
on public.extraction_runs(extraction_method);