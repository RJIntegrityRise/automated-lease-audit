insert into public.lease_checklist_items (
  item_code,
  section_name,
  field_name,
  description,
  check_type,
  required,
  severity,
  labels,
  configuration,
  sort_order
)
values

(
  'LEAD-DISCLOSURE',
  'Lead-Based Paint Disclosure',
  'Lead-Based Paint Disclosure',
  'Disclosure of Information on Lead-Based Paint and/or Lead-Based Paint Hazards.',
  'section_present',
  true,
  'high',
  '[
    "Disclosure of Information on Lead-Based Paint",
    "Lead-Based Paint Hazards",
    "Lead Based Paint"
  ]',
  '{}',
  10
),

(
  'LEASE-DATE',
  'Apartment Lease Contract',
  'Date of Lease Contract',
  'Date of the lease contract.',
  'date_present',
  true,
  'critical',
  '[
    "Date of Lease Contract",
    "Lease Contract Date",
    "Date of Lease"
  ]',
  '{}',
  20
),

(
  'LEASE-PARTIES',
  'Apartment Lease Contract',
  'Parties',
  'Lease parties must be identifiable.',
  'field_populated',
  true,
  'critical',
  '[
    "Parties",
    "Resident",
    "Residents",
    "Tenant",
    "Tenants"
  ]',
  '{}',
  30
),

(
  'LEASE-OCCUPANTS',
  'Apartment Lease Contract',
  'Occupants',
  'Occupants field should be present and reviewed.',
  'field_populated',
  true,
  'high',
  '[
    "Occupants",
    "Other Occupants"
  ]',
  '{}',
  40
),

(
  'LEASE-TERM',
  'Apartment Lease Contract',
  'Lease Term',
  'Lease term dates must be identifiable.',
  'date_present',
  true,
  'critical',
  '[
    "Lease Term",
    "Lease Start",
    "Lease End",
    "Beginning Date",
    "Ending Date"
  ]',
  '{}',
  50
),

(
  'LEASE-TERMINATION-NOTICE',
  'Apartment Lease Contract',
  'Termination Notice Requirements',
  'Termination or move-out notice requirement must be identifiable.',
  'number_present',
  true,
  'high',
  '[
    "Termination Notice",
    "Notice to Vacate",
    "Written Notice",
    "Notice of Non-Renewal"
  ]',
  '{
    "unit":"days"
  }',
  60
),

(
  'LEASE-SECURITY-DEPOSIT',
  'Apartment Lease Contract',
  'Security Deposit',
  'Security deposit amount must be identifiable.',
  'money_present',
  true,
  'high',
  '[
    "Security Deposit",
    "Deposit Amount"
  ]',
  '{}',
  70
),

(
  'LEASE-KEYS',
  'Apartment Lease Contract (Cont.)',
  'Keys',
  'Key information should be completed when applicable.',
  'field_populated',
  true,
  'medium',
  '[
    "Keys",
    "Key",
    "Access Devices"
  ]',
  '{}',
  80
),

(
  'LEASE-RENT-CHARGES',
  'Apartment Lease Contract (Cont.)',
  'Rent and Charges',
  'Rent and charge fields should contain values.',
  'money_present',
  true,
  'critical',
  '[
    "Rent and Charges",
    "Monthly Rent",
    "Base Rent",
    "Rent"
  ]',
  '{}',
  90
),

(
  'LEASE-UTILITIES',
  'Apartment Lease Contract (Cont.)',
  'Utilities',
  'Utility responsibility should be identified.',
  'field_populated',
  true,
  'high',
  '[
    "Utilities",
    "Utility Responsibility",
    "Utilities and Services"
  ]',
  '{}',
  100
),

(
  'LEASE-INSURANCE',
  'Apartment Lease Contract (Cont.)',
  'Insurance',
  'Insurance requirements should be identifiable.',
  'field_populated',
  true,
  'high',
  '[
    "Insurance",
    "Liability Insurance",
    "Renters Insurance"
  ]',
  '{}',
  110
),

(
  'LEASE-SPECIAL-PROVISIONS',
  'Special Provisions and What If Clauses',
  'Special Provisions',
  'Special provisions field should be detected and reviewed.',
  'field_populated',
  true,
  'medium',
  '[
    "Special Provisions",
    "Additional Provisions"
  ]',
  '{}',
  120
)

on conflict (item_code) do update
set
  section_name = excluded.section_name,
  field_name = excluded.field_name,
  description = excluded.description,
  check_type = excluded.check_type,
  required = excluded.required,
  severity = excluded.severity,
  labels = excluded.labels,
  configuration = excluded.configuration,
  sort_order = excluded.sort_order,
  enabled = true;


   insert into public.lease_checklist_items (
  item_code,
  section_name,
  field_name,
  description,
  check_type,
  required,
  severity,
  labels,
  configuration,
  sort_order
)
values

(
  'EARLY-TERM-DWELLING',
  'Choice of Damages / Early Termination Addendum',
  'Dwelling Unit Description',
  'Dwelling unit description must be identifiable.',
  'field_populated',
  true,
  'high',
  '[
    "Dwelling Unit Description",
    "Dwelling Description"
  ]',
  '{}',
  200
),

(
  'EARLY-TERM-RESIDENTS',
  'Choice of Damages / Early Termination Addendum',
  'Residents',
  'Residents must be identifiable.',
  'resident_names_present',
  true,
  'critical',
  '[
    "Residents",
    "Resident"
  ]',
  '{}',
  210
),

(
  'EARLY-TERM-CHOICE-1',
  'Choice of Damages / Early Termination Addendum',
  'Choice 1 Amount',
  'Choice 1 amount field should be completed when selected.',
  'money_present',
  false,
  'high',
  '[
    "Choice 1",
    "Choice One"
  ]',
  '{
    "conditional":true
  }',
  220
),

(
  'EARLY-TERM-CHOICE-2',
  'Choice of Damages / Early Termination Addendum',
  'Choice 2',
  'Choice 2 selection should be identifiable.',
  'checkbox_selected',
  false,
  'high',
  '[
    "Choice 2",
    "Choice Two"
  ]',
  '{
    "conditional":true
  }',
  230
),

(
  'ADD-SPECIAL-DWELLING',
  'Additional Special Provisions',
  'Dwelling Description',
  'Dwelling description should be completed.',
  'field_populated',
  true,
  'medium',
  '[
    "Dwelling Description"
  ]',
  '{}',
  240
),

(
  'ADD-SPECIAL-CONTRACT',
  'Additional Special Provisions',
  'Lease Contract Description',
  'Lease contract description should be completed.',
  'field_populated',
  true,
  'medium',
  '[
    "Lease Contract Description"
  ]',
  '{}',
  250
),

(
  'ADD-SPECIAL-RESIDENTS',
  'Additional Special Provisions',
  'Residents',
  'Residents should be identifiable.',
  'resident_names_present',
  true,
  'high',
  '[
    "Residents"
  ]',
  '{}',
  260
),

(
  'ADD-SPECIAL-FIELD',
  'Additional Special Provisions',
  'Special Provision Field',
  'Special provision field should be reviewed.',
  'field_populated',
  true,
  'medium',
  '[
    "Special Provision",
    "Special Provision Field"
  ]',
  '{}',
  270
)

on conflict (item_code) do update
set
  section_name = excluded.section_name,
  field_name = excluded.field_name,
  description = excluded.description,
  check_type = excluded.check_type,
  required = excluded.required,
  severity = excluded.severity,
  labels = excluded.labels,
  configuration = excluded.configuration,
  sort_order = excluded.sort_order,
  enabled = true;

  insert into public.lease_checklist_items (
  item_code,
  section_name,
  field_name,
  description,
  check_type,
  required,
  severity,
  labels,
  configuration,
  sort_order
)
values

(
  'INV-DWELLING',
  'Inventory and Condition Form',
  'Dwelling Description',
  'Dwelling description should be identifiable.',
  'field_populated',
  true,
  'medium',
  '["Dwelling Description","Dwelling Unit Description"]',
  '{}',
  300
),
(
  'INV-CONTRACT',
  'Inventory and Condition Form',
  'Lease Contract Description',
  'Lease contract description should be identifiable.',
  'field_populated',
  true,
  'medium',
  '["Lease Contract Description"]',
  '{}',
  310
),
(
  'INV-RESIDENTS',
  'Inventory and Condition Form',
  'Residents',
  'Resident names should be identifiable.',
  'resident_names_present',
  true,
  'high',
  '["Residents","Resident"]',
  '{}',
  320
),
(
  'INV-FORM-COMPLETE',
  'Inventory and Condition Form',
  'Editable Form Fields',
  'Editable inventory fields should be checked for completion.',
  'form_field_populated',
  true,
  'medium',
  '["Inventory and Condition Form"]',
  '{"inspect_all_form_fields":true}',
  330
),

(
  'UTILITY-ADDENDUM',
  'Utility and Services Addendum',
  'Utility and Services Addendum',
  'Utility and Services Addendum should be detected when applicable.',
  'section_present',
  false,
  'high',
  '["Utility and Services Addendum","Utilities and Services Addendum"]',
  '{"section":"utility_services_addendum"}',
  400
),
(
  'UTILITY-FORM-COMPLETE',
  'Utility and Services Addendum',
  'Editable Utility Fields',
  'Editable utility fields should be checked for completion.',
  'form_field_populated',
  false,
  'medium',
  '["Utility and Services Addendum"]',
  '{"inspect_all_form_fields":true,"conditional_section":"utility_services_addendum"}',
  410
),

(
  'AFFORDABLE-ADDENDUM',
  'Affordable Housing Addendum',
  'Affordable Housing Addendum',
  'Affordable housing addendum should be detected when applicable.',
  'section_present',
  false,
  'high',
  '["Government Regulated Affordable Housing Programs","Affordable Housing Programs"]',
  '{"section":"affordable_housing_addendum"}',
  500
),
(
  'AFFORDABLE-DWELLING',
  'Affordable Housing Addendum',
  'Dwelling Unit Description',
  'Dwelling unit description should be populated.',
  'field_populated',
  false,
  'medium',
  '["Dwelling Unit Description","Dwelling Description"]',
  '{"conditional_section":"affordable_housing_addendum"}',
  510
),
(
  'AFFORDABLE-CONTRACT',
  'Affordable Housing Addendum',
  'Lease Contract Description',
  'Lease contract description should be populated.',
  'field_populated',
  false,
  'medium',
  '["Lease Contract Description"]',
  '{"conditional_section":"affordable_housing_addendum"}',
  520
),
(
  'AFFORDABLE-RESIDENTS',
  'Affordable Housing Addendum',
  'Residents',
  'Resident names should be populated.',
  'resident_names_present',
  false,
  'high',
  '["Residents"]',
  '{"conditional_section":"affordable_housing_addendum"}',
  530
),

(
  'CONCESSION-ADDENDUM',
  'Rent Concession Addendum',
  'Rent Concession Addendum',
  'Rent concession or discount addendum should be detected when applicable.',
  'section_present',
  false,
  'high',
  '["Rent Concession","Rent Discount","Concession/Discount Agreement"]',
  '{"section":"rent_concession_addendum"}',
  600
),
(
  'CONCESSION-DWELLING',
  'Rent Concession Addendum',
  'Dwelling Unit Description',
  'Dwelling description should be populated.',
  'field_populated',
  false,
  'medium',
  '["Dwelling Unit Description","Dwelling Description"]',
  '{"conditional_section":"rent_concession_addendum"}',
  610
),
(
  'CONCESSION-CONTRACT',
  'Rent Concession Addendum',
  'Lease Contract Description',
  'Lease contract description should be populated.',
  'field_populated',
  false,
  'medium',
  '["Lease Contract Description"]',
  '{"conditional_section":"rent_concession_addendum"}',
  620
),
(
  'CONCESSION-RESIDENTS',
  'Rent Concession Addendum',
  'Residents',
  'Resident names should be populated.',
  'resident_names_present',
  false,
  'high',
  '["Residents"]',
  '{"conditional_section":"rent_concession_addendum"}',
  630
),
(
  'CONCESSION-AGREEMENT',
  'Rent Concession Addendum',
  'Concession/Discount Agreement',
  'Concession agreement should be identifiable.',
  'text_present',
  false,
  'high',
  '["Concession/Discount Agreement","Concession Agreement"]',
  '{"conditional_section":"rent_concession_addendum"}',
  640
),
(
  'CONCESSION-ONE-TIME',
  'Rent Concession Addendum',
  'One-time Concession',
  'One-time concession value should be checked when applicable.',
  'money_present',
  false,
  'medium',
  '["One-time Concession","One Time Concession"]',
  '{"conditional":true,"conditional_section":"rent_concession_addendum"}',
  650
),
(
  'CONCESSION-MONTHLY',
  'Rent Concession Addendum',
  'Monthly Discount/Concession',
  'Monthly discount or concession should be checked when applicable.',
  'money_present',
  false,
  'medium',
  '["Monthly Discount","Monthly Concession"]',
  '{"conditional":true,"conditional_section":"rent_concession_addendum"}',
  660
),
(
  'CONCESSION-OTHER',
  'Rent Concession Addendum',
  'Other Discount/Concession',
  'Other concession field should be checked when applicable.',
  'field_populated',
  false,
  'low',
  '["Other Discount","Other Concession"]',
  '{"conditional":true,"conditional_section":"rent_concession_addendum"}',
  670
),
(
  'CONCESSION-CHARGEBACK',
  'Rent Concession Addendum',
  'Concession Cancellation and Charge-Back',
  'Charge-back terms should be identifiable.',
  'text_present',
  false,
  'high',
  '["Concession Cancellation","Charge-Back","Charge Back"]',
  '{"conditional_section":"rent_concession_addendum"}',
  680
),
(
  'CONCESSION-SPECIAL',
  'Rent Concession Addendum',
  'Special Provisions',
  'Special provisions should be reviewed when present.',
  'field_populated',
  false,
  'medium',
  '["Special Provisions"]',
  '{"conditional_section":"rent_concession_addendum"}',
  690
),

(
  'INSURANCE-ADDENDUM',
  'Liability Insurance Addendum',
  'Liability Insurance Addendum',
  'Liability insurance addendum should be detected when applicable.',
  'section_present',
  false,
  'high',
  '["Liability Insurance Required Of Resident","Liability Insurance"]',
  '{"section":"liability_insurance_addendum"}',
  700
),
(
  'INSURANCE-DWELLING',
  'Liability Insurance Addendum',
  'Dwelling Description',
  'Dwelling description should be populated.',
  'field_populated',
  false,
  'medium',
  '["Dwelling Description"]',
  '{"conditional_section":"liability_insurance_addendum"}',
  710
),
(
  'INSURANCE-CONTRACT',
  'Liability Insurance Addendum',
  'Lease Contract Description',
  'Lease contract description should be populated.',
  'field_populated',
  false,
  'medium',
  '["Lease Contract Description"]',
  '{"conditional_section":"liability_insurance_addendum"}',
  720
),
(
  'INSURANCE-RESIDENTS',
  'Liability Insurance Addendum',
  'Residents',
  'Residents should be identifiable.',
  'resident_names_present',
  false,
  'high',
  '["Residents"]',
  '{"conditional_section":"liability_insurance_addendum"}',
  730
),
(
  'INSURANCE-SPECIAL',
  'Liability Insurance Addendum',
  'Special Provisions',
  'Special provisions should be checked.',
  'field_populated',
  false,
  'medium',
  '["Special Provisions"]',
  '{"conditional_section":"liability_insurance_addendum"}',
  740
),

(
  'NOSMOKE-ADDENDUM',
  'No-Smoking Addendum',
  'No-Smoking Addendum',
  'No-Smoking Addendum should be detected when applicable.',
  'section_present',
  false,
  'medium',
  '["No-Smoking Addendum","No Smoking Addendum"]',
  '{"section":"no_smoking_addendum"}',
  800
),
(
  'NOSMOKE-DWELLING',
  'No-Smoking Addendum',
  'Dwelling Description',
  'Dwelling description should be populated.',
  'field_populated',
  false,
  'medium',
  '["Dwelling Description"]',
  '{"conditional_section":"no_smoking_addendum"}',
  810
),
(
  'NOSMOKE-CONTRACT',
  'No-Smoking Addendum',
  'Lease Contract Description',
  'Lease contract description should be populated.',
  'field_populated',
  false,
  'medium',
  '["Lease Contract Description"]',
  '{"conditional_section":"no_smoking_addendum"}',
  820
),
(
  'NOSMOKE-RESIDENTS',
  'No-Smoking Addendum',
  'Residents',
  'Residents should be identifiable.',
  'resident_names_present',
  false,
  'medium',
  '["Residents"]',
  '{"conditional_section":"no_smoking_addendum"}',
  830
),

(
  'PARKING-ADDENDUM',
  'Resident Parking Addendum',
  'Resident Parking Addendum',
  'Parking addendum should be detected when applicable.',
  'section_present',
  false,
  'medium',
  '["Resident Parking Addendum","Parking Addendum"]',
  '{"section":"resident_parking_addendum"}',
  900
),
(
  'PARKING-DWELLING',
  'Resident Parking Addendum',
  'Dwelling Description',
  'Dwelling description should be populated.',
  'field_populated',
  false,
  'medium',
  '["Dwelling Description"]',
  '{"conditional_section":"resident_parking_addendum"}',
  910
),
(
  'PARKING-CONTRACT',
  'Resident Parking Addendum',
  'Lease Contract Description',
  'Lease contract description should be populated.',
  'field_populated',
  false,
  'medium',
  '["Lease Contract Description"]',
  '{"conditional_section":"resident_parking_addendum"}',
  920
),
(
  'PARKING-RESIDENTS',
  'Resident Parking Addendum',
  'Residents',
  'Residents should be identifiable.',
  'resident_names_present',
  false,
  'high',
  '["Residents"]',
  '{"conditional_section":"resident_parking_addendum"}',
  930
),
(
  'PARKING-BEGIN',
  'Resident Parking Addendum',
  'Begins on',
  'Parking start date should be populated.',
  'date_present',
  false,
  'medium',
  '["Begins on","Parking Begins"]',
  '{"conditional_section":"resident_parking_addendum"}',
  940
),
(
  'PARKING-END',
  'Resident Parking Addendum',
  'Ending on',
  'Parking end date should be populated.',
  'date_present',
  false,
  'medium',
  '["Ending on","Parking Ends"]',
  '{"conditional_section":"resident_parking_addendum"}',
  950
),
(
  'PARKING-COST',
  'Resident Parking Addendum',
  'Cost for Parking',
  'Parking cost should be populated.',
  'money_present',
  false,
  'medium',
  '["Cost for Parking","Parking Cost","Parking Fee"]',
  '{"conditional_section":"resident_parking_addendum"}',
  960
),
(
  'PARKING-SPECIAL',
  'Resident Parking Addendum',
  'Special Provisions',
  'Parking special provisions should be reviewed.',
  'field_populated',
  false,
  'low',
  '["Special Provisions"]',
  '{"conditional_section":"resident_parking_addendum"}',
  970
),

(
  'WASHER-ADDENDUM',
  'Washer and Dryer Addendum',
  'Washer and Dryer Addendum',
  'Washer and dryer addendum should be detected when applicable.',
  'section_present',
  false,
  'medium',
  '["Washer and Dryer Addendum","Washer & Dryer Addendum"]',
  '{"section":"washer_dryer_addendum"}',
  1000
),
(
  'WASHER-DWELLING',
  'Washer and Dryer Addendum',
  'Dwelling Unit Description',
  'Dwelling description should be populated.',
  'field_populated',
  false,
  'medium',
  '["Dwelling Unit Description","Dwelling Description"]',
  '{"conditional_section":"washer_dryer_addendum"}',
  1010
),
(
  'WASHER-CONTRACT',
  'Washer and Dryer Addendum',
  'Lease Contract Description',
  'Lease contract description should be populated.',
  'field_populated',
  false,
  'medium',
  '["Lease Contract Description"]',
  '{"conditional_section":"washer_dryer_addendum"}',
  1020
),
(
  'WASHER-RESIDENTS',
  'Washer and Dryer Addendum',
  'Residents',
  'Residents should be identifiable.',
  'resident_names_present',
  false,
  'medium',
  '["Residents"]',
  '{"conditional_section":"washer_dryer_addendum"}',
  1030
),
(
  'WASHER-FEE',
  'Washer and Dryer Addendum',
  'Washer and Dryer Rental Fees',
  'Washer and dryer rental fees should be populated.',
  'money_present',
  false,
  'high',
  '["Washer and Dryer Rental Fees","Washer Dryer Rental Fee","Rental Fees"]',
  '{"conditional_section":"washer_dryer_addendum"}',
  1040
)

on conflict (item_code) do update
set
  section_name = excluded.section_name,
  field_name = excluded.field_name,
  description = excluded.description,
  check_type = excluded.check_type,
  required = excluded.required,
  severity = excluded.severity,
  labels = excluded.labels,
  configuration = excluded.configuration,
  sort_order = excluded.sort_order,
  enabled = true;