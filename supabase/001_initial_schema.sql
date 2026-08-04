create extension if not exists "pgcrypto";

create type public.user_role as enum (
  'admin',
  'manager',
  'reviewer'
);

create type public.lease_status as enum (
  'uploaded',
  'extracting',
  'auditing',
  'completed',
  'failed'
);

create type public.audit_status as enum (
  'pending',
  'processing',
  'completed',
  'failed'
);

create type public.finding_severity as enum (
  'critical',
  'high',
  'medium',
  'low',
  'informational'
);

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text,
  role public.user_role not null default 'reviewer',
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.properties (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  address_line_1 text,
  address_line_2 text,
  city text,
  state text,
  postal_code text,
  created_by uuid references public.profiles(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.leases (
  id uuid primary key default gen_random_uuid(),
  internal_lease_id text,
  property_id uuid references public.properties(id),
  unit_number text,
  tenant_names text[] not null default '{}',
  status public.lease_status not null default 'uploaded',
  monthly_rent numeric(12, 2),
  security_deposit numeric(12, 2),
  lease_start_date date,
  lease_end_date date,
  extraction_confidence numeric(5, 4),
  processing_error text,
  uploaded_by uuid not null references public.profiles(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  constraint extraction_confidence_range
    check (
      extraction_confidence is null
      or extraction_confidence between 0 and 1
    )
);

create table public.lease_documents (
  id uuid primary key default gen_random_uuid(),
  lease_id uuid not null references public.leases(id) on delete cascade,
  storage_path text not null unique,
  original_filename text not null,
  mime_type text not null,
  file_size_bytes bigint,
  page_count integer,
  extracted_text text,
  uploaded_by uuid not null references public.profiles(id),
  created_at timestamptz not null default now()
);

create table public.extracted_fields (
  id uuid primary key default gen_random_uuid(),
  lease_id uuid not null references public.leases(id) on delete cascade,
  field_name text not null,
  field_value jsonb,
  page_number integer,
  source_text text,
  confidence numeric(5, 4),
  created_at timestamptz not null default now(),

  constraint field_confidence_range
    check (
      confidence is null
      or confidence between 0 and 1
    )
);

create table public.audit_rules (
  id uuid primary key default gen_random_uuid(),
  rule_code text not null unique,
  name text not null,
  description text,
  category text not null,
  severity public.finding_severity not null,
  configuration jsonb not null default '{}'::jsonb,
  enabled boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.audits (
  id uuid primary key default gen_random_uuid(),
  lease_id uuid not null references public.leases(id) on delete cascade,
  status public.audit_status not null default 'pending',
  score integer,
  critical_count integer not null default 0,
  high_count integer not null default 0,
  medium_count integer not null default 0,
  low_count integer not null default 0,
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz not null default now(),

  constraint audit_score_range
    check (score is null or score between 0 and 100)
);

create table public.audit_findings (
  id uuid primary key default gen_random_uuid(),
  audit_id uuid not null references public.audits(id) on delete cascade,
  rule_id uuid references public.audit_rules(id),
  severity public.finding_severity not null,
  title text not null,
  explanation text not null,
  page_numbers integer[] not null default '{}',
  evidence jsonb not null default '{}'::jsonb,
  requires_review boolean not null default true,
  resolved boolean not null default false,
  resolution_notes text,
  resolved_by uuid references public.profiles(id),
  resolved_at timestamptz,
  created_at timestamptz not null default now()
);

create index properties_created_by_idx
  on public.properties(created_by);

create index leases_property_id_idx
  on public.leases(property_id);

create index leases_uploaded_by_idx
  on public.leases(uploaded_by);

create index leases_status_idx
  on public.leases(status);

create index lease_documents_lease_id_idx
  on public.lease_documents(lease_id);

create index extracted_fields_lease_id_idx
  on public.extracted_fields(lease_id);

create index extracted_fields_name_idx
  on public.extracted_fields(field_name);

create index audits_lease_id_idx
  on public.audits(lease_id);

create index audit_findings_audit_id_idx
  on public.audit_findings(audit_id);

create index audit_findings_severity_idx
  on public.audit_findings(severity);