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
  'DOC-OCR-001',
  'Scanned pages require review',
  'OCR-processed pages should be reviewed when important lease information depends on OCR.',
  'document_quality',
  'low',
  '{
    "field":"ocr_used",
    "operator":"equals",
    "value":false
  }',
  false
),
(
  'SIG-IMAGE-001',
  'Graphical signature review',
  'A possible graphical signature mark requires manual confirmation when it cannot be matched deterministically.',
  'signatures',
  'medium',
  '{
    "field":"signature_image_review_required",
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