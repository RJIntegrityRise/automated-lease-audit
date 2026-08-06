alter table public.audit_findings
add column if not exists status text not null default 'failed';

alter table public.audit_findings
add column if not exists field_name text;

alter table public.audit_findings
add column if not exists actual_value jsonb;

alter table public.audit_findings
add column if not exists expected_value jsonb;

alter table public.audits
add column if not exists informational_count integer not null default 0;

alter table public.audits
add column if not exists total_findings integer not null default 0;

alter table public.audits
add column if not exists recommendation text;

alter table public.audits
add column if not exists model_version text;

create index if not exists audits_created_at_idx
on public.audits(created_at desc);

create index if not exists audit_findings_rule_id_idx
on public.audit_findings(rule_id);