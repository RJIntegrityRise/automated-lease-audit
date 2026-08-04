insert into public.audit_rules (
  rule_code,
  name,
  description,
  category,
  severity,
  configuration
)
values
(
  'CORE-001',
  'Tenant name required',
  'At least one tenant name must be identifiable in the lease.',
  'critical_information',
  'high',
  '{"field":"tenant_names","operator":"is_not_empty"}'
),
(
  'CORE-002',
  'Unit number required',
  'The leased unit must be identifiable.',
  'critical_information',
  'high',
  '{"field":"unit_number","operator":"is_not_empty"}'
),
(
  'DATE-001',
  'Lease start date required',
  'The lease must contain a start date.',
  'dates',
  'high',
  '{"field":"lease_start_date","operator":"is_not_empty"}'
),
(
  'DATE-002',
  'Lease end date required',
  'The lease must contain an end date.',
  'dates',
  'high',
  '{"field":"lease_end_date","operator":"is_not_empty"}'
),
(
  'DATE-003',
  'Lease dates must be valid',
  'The lease end date must occur after the start date.',
  'dates',
  'critical',
  '{"left_field":"lease_end_date","operator":"greater_than","right_field":"lease_start_date"}'
),
(
  'FIN-001',
  'Monthly rent required',
  'The monthly rent amount must be identifiable.',
  'financial',
  'critical',
  '{"field":"monthly_rent","operator":"is_not_empty"}'
),
(
  'FIN-002',
  'Security deposit required',
  'The security deposit must be identifiable.',
  'financial',
  'medium',
  '{"field":"security_deposit","operator":"is_not_empty"}'
);