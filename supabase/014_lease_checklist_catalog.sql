create table if not exists public.lease_checklist_items (
  id uuid primary key default gen_random_uuid(),

  item_code text not null unique,

  section_name text not null,
  field_name text not null,

  description text,

  check_type text not null,
  required boolean not null default true,

  severity text not null default 'medium',

  labels jsonb not null default '[]'::jsonb,

  configuration jsonb not null default '{}'::jsonb,

  enabled boolean not null default true,

  sort_order integer not null default 0,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  constraint lease_checklist_check_type
    check (
      check_type in (
        'section_present',
        'text_present',
        'field_populated',
        'date_present',
        'money_present',
        'number_present',
        'checkbox_selected',
        'form_field_populated',
        'signature_present',
        'signature_date_present',
        'resident_names_present'
      )
    ),

  constraint lease_checklist_severity
    check (
      severity in (
        'critical',
        'high',
        'medium',
        'low',
        'informational'
      )
    )
);

create index if not exists lease_checklist_section_idx
on public.lease_checklist_items(section_name);

create index if not exists lease_checklist_enabled_idx
on public.lease_checklist_items(enabled);