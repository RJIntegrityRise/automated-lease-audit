create table if not exists public.exception_reports (
  id uuid primary key default gen_random_uuid(),

  lease_id uuid not null
    references public.leases(id)
    on delete cascade,

  extraction_run_id uuid not null
    references public.extraction_runs(id)
    on delete cascade,

  audit_id uuid
    references public.audits(id)
    on delete set null,

  status text not null default 'draft',

  title text not null,

  exception_count integer not null default 0,

  critical_count integer not null default 0,
  high_count integer not null default 0,
  medium_count integer not null default 0,
  low_count integer not null default 0,

  report_data jsonb not null,

  published_at timestamptz,

  created_at timestamptz not null default now(),

  constraint exception_report_status
    check (
      status in (
        'draft',
        'published'
      )
    )
);

create index if not exists exception_reports_lease_idx
on public.exception_reports(lease_id);

create index if not exists exception_reports_run_idx
on public.exception_reports(extraction_run_id);