export type SessionUser = {
  id: string;
  email: string;
  role: string;
  locale: string;
};

export type Profile = {
  id: string;
  user_id: string;
  user_type: string | null;
  country: string;
  region: string | null;
  province: string | null;
  age_range: string | null;
  business_exists: boolean | null;
  legal_entity_type: string | null;
  company_age_band: string | null;
  company_size_band: string | null;
  revenue_band: string | null;
  sector_code_or_category: string | null;
  founder_attributes: Record<string, unknown> | null;
  hiring_intent: boolean | null;
  innovation_intent: boolean | null;
  sustainability_intent: boolean | null;
  export_intent: boolean | null;
  incorporation_status: string | null;
  startup_stage: string | null;
  goals: string[] | null;
  fact_values?: Record<string, unknown> | null;
  profile_completeness_score: number;
  updated_at: string;
};

export type ProfileQuestion = {
  key: string;
  label: string;
  step: number;
  kind: string;
  required: boolean;
  options?: string[];
  helper_text?: string | null;
  audience?: string[] | null;
  module?: string | null;
  sensitive?: boolean;
  depends_on?: Record<string, unknown> | null;
  ask_when_measure_families?: string[] | null;
  why_needed?: string | null;
  coverage_weight?: number;
  ambiguity_reduction_score?: number;
};

export type OpportunityCard = {
  id: string;
  slug: string;
  title: string;
  short_description: string;
  category: string;
  geography_scope: string;
  benefit_type: string;
  match_status: string | null;
  match_score: number | null;
  user_visible_reasoning: string | null;
  missing_fields: string[];
  deadline_date: string | null;
  estimated_value_max: number | null;
  last_checked_at: string;
  is_saved: boolean;
};

export type OpportunityDetail = OpportunityCard & {
  long_description: string | null;
  issuer_name: string;
  official_links: string[];
  source_documents: string[];
  evidence_snippets: { source: string; quote: string; field: string }[];
  required_documents: string[] | null;
  next_steps: string[];
  why_this_matches: string[];
  what_is_missing: string[];
  verification_status: string;
};

export type NotificationPreferences = {
  email_enabled: boolean;
  weekly_profile_nudges: boolean;
  deadline_reminders: boolean;
  new_opportunity_alerts: boolean;
  source_change_digests: boolean;
};

export type NotificationHistoryItem = {
  id: string;
  event_type: string;
  opportunity_id: string | null;
  status: string;
  recipient: string;
  subject: string;
  created_at: string;
  sent_at: string | null;
  error_message: string | null;
};

export type Source = {
  id: string;
  source_name: string;
  source_type: string;
  authority_level: string;
  crawl_method: string;
  crawl_frequency: string;
  trust_level: string;
  region: string;
  status: string;
  created_at: string;
};

export type IngestionRun = {
  id: string;
  source_endpoint_id: string;
  stage: string;
  status: string;
  started_at: string;
  finished_at?: string | null;
  diagnostics?: Record<string, unknown> | null;
};

export type ReviewItem = {
  id: string;
  item_type: string;
  status: string;
  related_entity_type: string;
  related_entity_id: string;
  title: string;
  description?: string | null;
  payload?: Record<string, unknown> | null;
  created_at: string;
  resolved_at?: string | null;
};

export type RuleListItem = {
  id: string;
  note: string | null;
  is_active: boolean;
  version_number: number;
  opportunity_title: string;
  fixture_count: number;
};

export type RuleTestResult = {
  rule_id: string;
  passed: boolean;
  results: {
    case_id: string;
    name: string;
    scenario_type: string;
    expected_status: string;
    actual_status: string;
    passed: boolean;
    missing_fields: string[];
  }[];
};

export type MeasureFamily = {
  id: string;
  slug: string;
  title: string;
  operator_name: string;
  source_domain: string;
  is_regime_only: boolean;
  is_actionable: boolean;
  current_lifecycle_status: string;
  benefit_kind: string | null;
  benefit_magnitude_model: string | null;
  geography: string;
  legal_basis_references: string[];
  beneficiary_entity_types: string[];
  requirements_count: number;
  documents_count: number;
  primary_legal_basis_count: number;
  primary_operational_count: number;
  verification_timestamp: string;
};

export type AdminDocument = {
  id: string;
  family_slug: string;
  family_title: string;
  source_domain: string;
  document_title: string | null;
  canonical_url: string | null;
  document_role: string;
  lifecycle_status: string;
  relationship_type: string;
  is_primary_legal_basis: boolean;
  is_primary_operational_doc: boolean;
  created_at: string;
};

export type SurveyCoverageRow = {
  fact_key: string;
  label: string;
  module: string;
  sensitive: boolean;
  stable: boolean;
  coverage_weight: number;
  ambiguity_reduction_score: number;
  active_measure_family_count: number;
  hard_requirement_count: number;
  project_requirement_count: number;
  person_requirement_count: number;
  ranking_requirement_count: number;
  ask_when_measure_families: string[];
  depends_on?: Record<string, unknown> | null;
};

export type SurveyCoverageSnapshot = {
  id: string;
  snapshot_key: string;
  created_at: string;
  total_measure_families: number;
  total_active_measure_families: number;
  rows: SurveyCoverageRow[];
};

export type BootstrapRunResult = {
  measure_families_seeded: number;
  documents_seeded: number;
  facts_seeded: number;
  coverage_rows: number;
  review_message: string;
};

export type IntegrityCheck = {
  name: string;
  duplicate_group_count: number;
  duplicate_row_count: number;
  sample_values: string[];
};

export type AdminIntegritySnapshot = {
  current_revision: string | null;
  head_revision: string;
  schema_current: boolean;
  checks: IntegrityCheck[];
};
