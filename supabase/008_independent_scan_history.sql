create type public.extraction_status as enum (
  'pending',
  'processing',
  'completed',
  'failed'
);

create table public.extraction_runs (
  id uuid primary key default gen_random_uuid(),

  lease_id uuid not null
    references public.leases(id)
    on delete cascade,

  document_id uuid not null
    references public.lease_documents(id)
    on delete cascade,

  status public.extraction_status not null default 'pending',

  provider text not null,
  model_name text not null,

  structured_data jsonb,
  overall_confidence numeric(5, 4),

  processing_error text,

  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz not null default now(),

  constraint extraction_run_confidence_range
    check (
      overall_confidence is null
      or overall_confidence between 0 and 1
    )
);

alter table public.extracted_fields
add column if not exists extraction_run_id uuid
references public.extraction_runs(id)
on delete cascade;

alter table public.audits
add column if not exists extraction_run_id uuid
references public.extraction_runs(id);

create index extraction_runs_lease_id_idx
on public.extraction_runs(lease_id);

create index extraction_runs_document_id_idx
on public.extraction_runs(document_id);

create index extraction_runs_created_at_idx
on public.extraction_runs(created_at desc);

create index extracted_fields_extraction_run_id_idx
on public.extracted_fields(extraction_run_id);

create index audits_extraction_run_id_idx
on public.audits(extraction_run_id);