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
  'CORE-START-DATE',
  'Lease start date required',
  'A lease start date must be detected.',
  'dates',
  'critical',
  '{
    "field":"lease_start_date.status",
    "operator":"equals",
    "value":"detected"
  }',
  true
),
(
  'CORE-END-DATE',
  'Lease end date required',
  'A lease end date must be detected.',
  'dates',
  'critical',
  '{
    "field":"lease_end_date.status",
    "operator":"equals",
    "value":"detected"
  }',
  true
),
(
  'CORE-RENT',
  'Monthly rent required',
  'A positive monthly rent amount must be detected.',
  'financial',
  'critical',
  '{
    "field":"monthly_rent.status",
    "operator":"equals",
    "value":"detected"
  }',
  true
),
(
  'CORE-DEPOSIT',
  'Security deposit review',
  'The security deposit should be detected or manually reviewed.',
  'financial',
  'medium',
  '{
    "field":"security_deposit.status",
    "operator":"equals",
    "value":"detected"
  }',
  true
),
(
  'SIG-TENANT',
  'Tenant signature detection',
  'A tenant signature must be detected.',
  'signatures',
  'critical',
  '{
    "field":"tenant_signature.status",
    "operator":"equals",
    "value":"detected"
  }',
  true
),
(
  'SIG-LANDLORD',
  'Landlord signature detection',
  'A landlord or authorized representative signature must be detected.',
  'signatures',
  'high',
  '{
    "field":"landlord_signature.status",
    "operator":"equals",
    "value":"detected"
  }',
  true
),
(
  'SIG-TENANT-DATE',
  'Tenant signature date',
  'A tenant signature date should be detected.',
  'signatures',
  'high',
  '{
    "field":"tenant_signature_date.status",
    "operator":"equals",
    "value":"detected"
  }',
  true
),
(
  'SIG-LANDLORD-DATE',
  'Landlord signature date',
  'A landlord signature date should be detected.',
  'signatures',
  'medium',
  '{
    "field":"landlord_signature_date.status",
    "operator":"equals",
    "value":"detected"
  }',
  true
),
(
  'NOTICE-REQUIRED',
  'Notice period required',
  'A notice period should be detected.',
  'termination',
  'medium',
  '{
    "field":"notice_period_days.status",
    "operator":"equals",
    "value":"detected"
  }',
  true
),
(
  'DOC-READABLE',
  'Readable lease text',
  'The lease must contain readable text or be sent to OCR.',
  'document_quality',
  'critical',
  '{
    "field":"possible_scanned_document",
    "operator":"equals",
    "value":false
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