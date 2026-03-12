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
