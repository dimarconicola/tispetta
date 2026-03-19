from datetime import datetime

from app.schemas.common import ApiModel


class MeasureFamilyRead(ApiModel):
    id: str
    slug: str
    title: str
    operator_name: str
    source_domain: str
    is_regime_only: bool
    is_actionable: bool
    current_lifecycle_status: str
    benefit_kind: str | None = None
    benefit_magnitude_model: str | None = None
    geography: str
    legal_basis_references: list[str]
    beneficiary_entity_types: list[str]
    requirements_count: int
    documents_count: int
    primary_legal_basis_count: int
    primary_operational_count: int
    verification_timestamp: datetime


class AdminDocumentRead(ApiModel):
    id: str
    family_slug: str
    family_title: str
    source_domain: str
    document_title: str | None = None
    canonical_url: str | None = None
    document_role: str
    lifecycle_status: str
    relationship_type: str
    is_primary_legal_basis: bool
    is_primary_operational_doc: bool
    created_at: datetime


class SurveyCoverageRow(ApiModel):
    fact_key: str
    label: str
    module: str
    sensitive: bool
    stable: bool
    coverage_weight: float
    ambiguity_reduction_score: float
    active_measure_family_count: int
    hard_requirement_count: int
    project_requirement_count: int
    person_requirement_count: int
    ranking_requirement_count: int
    ask_when_measure_families: list[str]
    depends_on: dict | None = None


class SurveyCoverageSnapshotRead(ApiModel):
    id: str
    snapshot_key: str
    created_at: datetime
    total_measure_families: int
    total_active_measure_families: int
    rows: list[SurveyCoverageRow]


class BootstrapRunResult(ApiModel):
    measure_families_seeded: int
    documents_seeded: int
    facts_seeded: int
    coverage_rows: int
    review_message: str


class IntegrityCheckRead(ApiModel):
    name: str
    duplicate_group_count: int
    duplicate_row_count: int
    sample_values: list[str]


class AdminIntegrityRead(ApiModel):
    current_revision: str | None = None
    head_revision: str
    schema_current: bool
    checks: list[IntegrityCheckRead]
