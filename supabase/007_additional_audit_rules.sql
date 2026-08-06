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
  'CORE-003',
  'Property name required',
  'The property name should be identifiable in the lease.',
  'critical_information',
  'medium',
  '{"field":"property_name","operator":"is_not_empty"}',
  true
),
(
  'DATE-004',
  'Lease term must be positive',
  'The lease end date must occur after the lease start date.',
  'dates',
  'critical',
  '{"left_field":"lease_end_date","operator":"greater_than","right_field":"lease_start_date"}',
  true
),
(
  'FIN-003',
  'Monthly rent must be positive',
  'Monthly rent must be greater than zero.',
  'financial',
  'critical',
  '{"field":"monthly_rent","operator":"greater_than","value":0}',
  true
),
(
  'FIN-004',
  'Security deposit must not be negative',
  'Security deposit cannot be negative.',
  'financial',
  'high',
  '{"field":"security_deposit","operator":"greater_than_or_equal","value":0}',
  true
),
(
  'SIG-001',
  'Tenant signatures required',
  'All named tenants should have signed the lease.',
  'signatures',
  'critical',
  '{"field":"tenant_signatures_complete","operator":"equals","value":true}',
  true
),
(
  'SIG-002',
  'Landlord signature required',
  'The landlord or authorized representative should sign the lease.',
  'signatures',
  'high',
  '{"field":"landlord_signed","operator":"equals","value":true}',
  true
),
(
  'DOC-001',
  'Notice period required',
  'The lease should contain a tenant notice period.',
  'document',
  'medium',
  '{"field":"notice_period_days","operator":"is_not_empty"}',
  true
),
(
  'AI-001',
  'Low-confidence extraction review',
  'Low-confidence extracted data requires manual verification.',
  'data_quality',
  'medium',
  '{"field":"overall_confidence","operator":"greater_than_or_equal","value":0.75}',
  true
)
on conflict (rule_code) do nothing;