insert into public.audit_rules (
  rule_code,
  name,
  description,
  category,
  severity,
  configuration,
  enabled
)
values
(
  'SIG-TENANT-NAMES',
  'Tenant names must be identifiable',
  'At least one tenant name must be detected for signature matching.',
  'signatures',
  'high',
  '{
    "field":"tenant_names",
    "operator":"is_not_empty"
  }',
  true
),
(
  'SIG-ALL-TENANTS',
  'Every named tenant must have a signature',
  'Each tenant named in the lease must have a matching detected signature record.',
  'signatures',
  'critical',
  '{
    "field":"all_named_tenants_signed.status",
    "operator":"equals",
    "value":"detected"
  }',
  true
),
(
  'SIG-UNMATCHED-TENANTS',
  'No unmatched tenant names',
  'Every named tenant should be matched to a signature record.',
  'signatures',
  'critical',
  '{
    "field":"unmatched_tenant_names",
    "operator":"is_empty"
  }',
  true
),
(
  'SIG-UNMATCHED-SIGNATURES',
  'No unidentified tenant signatures',
  'Detected tenant signature names should match the tenant list.',
  'signatures',
  'medium',
  '{
    "field":"unmatched_signature_names",
    "operator":"is_empty"
  }',
  true
)
on conflict (rule_code) do update
set
  name = excluded.name,
  description = excluded.description,
  category = excluded.category,
  severity = excluded.severity,
  configuration = excluded.configuration,
  enabled = excluded.enabled;