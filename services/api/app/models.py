from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Role(StrEnum):
    USER = 'user'
    ADMIN = 'admin'


class UserType(StrEnum):
    FREELANCER = 'freelancer'
    STARTUP = 'startup'
    SME = 'sme'
    ADVISOR = 'advisor'


class MatchStatus(StrEnum):
    CONFIRMED = 'confirmed'
    LIKELY = 'likely'
    UNCLEAR = 'unclear'
    NOT_ELIGIBLE = 'not_eligible'


class OpportunityType(StrEnum):
    GRANT = 'grant'
    SUBSIDIZED_LOAN = 'subsidized_loan'
    TAX_INCENTIVE = 'tax_incentive'
    HIRING_INCENTIVE = 'hiring_incentive'
    TRAINING = 'training_incentive'
    DIGITIZATION = 'digitization_incentive'
    SUSTAINABILITY = 'sustainability_incentive'
    EXPORT = 'export_incentive'


class VerificationStatus(StrEnum):
    DRAFT = 'draft'
    REVIEWED = 'reviewed'
    AUTO_VERIFIED = 'auto_verified'
    NEEDS_REVIEW = 'needs_review'


class RecordStatus(StrEnum):
    DRAFT = 'draft'
    PUBLISHED = 'published'
    UNPUBLISHED = 'unpublished'


class SourceType(StrEnum):
    WEBSITE = 'website'
    PDF = 'pdf'
    API = 'api'


class CrawlMethod(StrEnum):
    HTTP = 'http'
    HTML = 'html'
    PDF = 'pdf'
    PLAYWRIGHT = 'playwright'


class ReviewItemType(StrEnum):
    LOW_CONFIDENCE = 'low_confidence'
    CONFLICT = 'conflict'
    MISSING_RULE = 'missing_rule'
    PUBLISH_PENDING = 'publish_pending'
    FAILED_RULE_TEST = 'failed_rule_test'
    USER_DISPUTE = 'user_dispute'


class ReviewStatus(StrEnum):
    OPEN = 'open'
    RESOLVED = 'resolved'


class NotificationChannel(StrEnum):
    EMAIL = 'email'


class NotificationStatus(StrEnum):
    PENDING = 'pending'
    SENT = 'sent'
    FAILED = 'failed'
    SUPPRESSED = 'suppressed'


class IngestionStage(StrEnum):
    FETCH = 'fetch'
    NORMALIZE = 'normalize'
    CLASSIFY = 'classify'
    EXTRACT = 'extract'
    VERIFY = 'verify'
    COMPLETE = 'complete'
    FAILED = 'failed'


class DocumentRole(StrEnum):
    LEGAL_BASIS = 'legal_basis'
    IMPLEMENTING_DECREE = 'implementing_decree'
    MINISTERIAL_CIRCULAR = 'ministerial_circular'
    OPERATOR_MEASURE_PAGE = 'operator_measure_page'
    FAQ_OR_OPERATIONAL_GUIDE = 'faq_or_operational_guide'
    APPLICATION_PORTAL = 'application_portal'
    FORMS_AND_TEMPLATES = 'forms_and_templates'
    NEWS_OR_STATUS_UPDATE = 'news_or_status_update'
    IRRELEVANT = 'irrelevant'


class MeasureLifecycleStatus(StrEnum):
    EVERGREEN_REGIME = 'evergreen_regime'
    OPEN_APPLICATION = 'open_application'
    SCHEDULED = 'scheduled'
    PAUSED = 'paused'
    EXHAUSTED = 'exhausted'
    CLOSED = 'closed'
    HISTORICAL_REFERENCE = 'historical_reference'


class SurveyModule(StrEnum):
    CORE_ENTITY = 'core_entity'
    STRATEGIC_INTENT = 'strategic_intent'
    CONDITIONAL_ACCURACY = 'conditional_accuracy'


class RequirementMode(StrEnum):
    ENTITY_HARD_REQUIREMENT = 'entity_hard_requirement'
    PROJECT_HARD_REQUIREMENT = 'project_hard_requirement'
    PERSON_SPECIFIC_REQUIREMENT = 'person_specific_requirement'
    RANKING_OR_BOOSTER = 'ranking_or_booster'


class FactValueKind(StrEnum):
    SELECT = 'select'
    BOOLEAN = 'boolean'
    TEXT = 'text'
    NUMBER = 'number'


class User(Base):
    __tablename__ = 'users'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(32), default=Role.USER.value)
    locale: Mapped[str] = mapped_column(String(12), default='it-IT')
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    profile: Mapped['Profile | None'] = relationship(back_populates='user', uselist=False)
    notification_preferences: Mapped['NotificationPreference | None'] = relationship(back_populates='user', uselist=False)


class MagicLinkToken(Base):
    __tablename__ = 'magic_link_tokens'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(255), index=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Profile(Base):
    __tablename__ = 'profiles'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), unique=True, index=True)
    user_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    country: Mapped[str] = mapped_column(String(2), default='IT')
    region: Mapped[str | None] = mapped_column(String(128), nullable=True)
    province: Mapped[str | None] = mapped_column(String(128), nullable=True)
    age_range: Mapped[str | None] = mapped_column(String(64), nullable=True)
    business_exists: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    legal_entity_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    company_age_band: Mapped[str | None] = mapped_column(String(64), nullable=True)
    company_size_band: Mapped[str | None] = mapped_column(String(64), nullable=True)
    revenue_band: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sector_code_or_category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    founder_attributes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    hiring_intent: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    innovation_intent: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    sustainability_intent: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    export_intent: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    incorporation_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    startup_stage: Mapped[str | None] = mapped_column(String(64), nullable=True)
    goals: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    profile_completeness_score: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    user: Mapped['User'] = relationship(back_populates='profile')
    revisions: Mapped[list['ProfileRevision']] = relationship(back_populates='profile')
    fact_values: Mapped[list['ProfileFactValue']] = relationship(back_populates='profile')


class ProfileRevision(Base):
    __tablename__ = 'profile_revisions'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    profile_id: Mapped[str] = mapped_column(ForeignKey('profiles.id'), index=True)
    revision_number: Mapped[int] = mapped_column(Integer, default=1)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    profile: Mapped['Profile'] = relationship(back_populates='revisions')


class Source(Base):
    __tablename__ = 'sources'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    source_name: Mapped[str] = mapped_column(String(255))
    source_type: Mapped[str] = mapped_column(String(32), default=SourceType.WEBSITE.value)
    authority_level: Mapped[str] = mapped_column(String(32), default='tier_1')
    crawl_method: Mapped[str] = mapped_column(String(32), default=CrawlMethod.HTML.value)
    crawl_frequency: Mapped[str] = mapped_column(String(64), default='daily')
    trust_level: Mapped[str] = mapped_column(String(32), default='high')
    region: Mapped[str] = mapped_column(String(128), default='Italy')
    status: Mapped[str] = mapped_column(String(32), default='active')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    endpoints: Mapped[list['SourceEndpoint']] = relationship(back_populates='source')


class SourceEndpoint(Base):
    __tablename__ = 'source_endpoints'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    source_id: Mapped[str] = mapped_column(ForeignKey('sources.id'), index=True)
    name: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(Text)
    document_type: Mapped[str] = mapped_column(String(64), default='opportunity_page')
    status: Mapped[str] = mapped_column(String(32), default='active')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    source: Mapped['Source'] = relationship(back_populates='endpoints')


class SourceSnapshot(Base):
    __tablename__ = 'source_snapshots'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    source_endpoint_id: Mapped[str] = mapped_column(ForeignKey('source_endpoints.id'), index=True)
    checksum: Mapped[str] = mapped_column(String(128), index=True)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    headers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    storage_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    diagnostics: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class NormalizedDocument(Base):
    __tablename__ = 'normalized_documents'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    source_snapshot_id: Mapped[str] = mapped_column(ForeignKey('source_snapshots.id'), index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    canonical_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    clean_text: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    structural_sections: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    document_type: Mapped[str] = mapped_column(String(64), default='opportunity_page')
    document_role: Mapped[str] = mapped_column(String(64), default=DocumentRole.IRRELEVANT.value)
    lifecycle_status: Mapped[str] = mapped_column(String(64), default=MeasureLifecycleStatus.HISTORICAL_REFERENCE.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    family_links: Mapped[list['MeasureFamilyDocument']] = relationship(back_populates='document')


class MeasureFamily(Base):
    __tablename__ = 'measure_families'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    operator_name: Mapped[str] = mapped_column(String(255))
    source_domain: Mapped[str] = mapped_column(String(255))
    is_regime_only: Mapped[bool] = mapped_column(Boolean, default=False)
    is_actionable: Mapped[bool] = mapped_column(Boolean, default=True)
    current_version_id: Mapped[str | None] = mapped_column(ForeignKey('measure_family_versions.id'), nullable=True)
    current_lifecycle_status: Mapped[str] = mapped_column(String(64), default=MeasureLifecycleStatus.HISTORICAL_REFERENCE.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    versions: Mapped[list['MeasureFamilyVersion']] = relationship(
        back_populates='family',
        foreign_keys='MeasureFamilyVersion.measure_family_id',
    )
    current_version: Mapped['MeasureFamilyVersion | None'] = relationship(
        foreign_keys=[current_version_id],
        post_update=True,
    )
    documents: Mapped[list['MeasureFamilyDocument']] = relationship(back_populates='family')


class MeasureFamilyVersion(Base):
    __tablename__ = 'measure_family_versions'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    measure_family_id: Mapped[str] = mapped_column(ForeignKey('measure_families.id'), index=True)
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    title: Mapped[str] = mapped_column(String(255))
    operator_name: Mapped[str] = mapped_column(String(255))
    benefit_kind: Mapped[str | None] = mapped_column(String(128), nullable=True)
    benefit_magnitude_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    lifecycle_status: Mapped[str] = mapped_column(String(64), default=MeasureLifecycleStatus.HISTORICAL_REFERENCE.value)
    geography: Mapped[str] = mapped_column(String(128), default='Italy')
    legal_basis_references: Mapped[list[str]] = mapped_column(JSON)
    beneficiary_entity_types: Mapped[list[str]] = mapped_column(JSON)
    size_constraints: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    sector_constraints: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    legal_form_constraints: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    regime_status_constraints: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    age_or_time_constraints: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    person_specific_constraints: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    project_specific_constraints: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    application_mechanics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    required_documents: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    evidence_snippets: Mapped[list[dict]] = mapped_column(JSON)
    entrypoint_urls: Mapped[list[str]] = mapped_column(JSON)
    allowed_path_keywords: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    verification_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    changed_fields: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    family: Mapped['MeasureFamily'] = relationship(
        back_populates='versions',
        foreign_keys=[measure_family_id],
    )
    requirements: Mapped[list['MeasureFamilyRequirement']] = relationship(back_populates='family_version')


class MeasureFamilyDocument(Base):
    __tablename__ = 'measure_family_documents'
    __table_args__ = (UniqueConstraint('measure_family_id', 'normalized_document_id', name='uq_family_document'),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    measure_family_id: Mapped[str] = mapped_column(ForeignKey('measure_families.id'), index=True)
    normalized_document_id: Mapped[str] = mapped_column(ForeignKey('normalized_documents.id'), index=True)
    relationship_type: Mapped[str] = mapped_column(String(64), default='supporting_document')
    is_primary_legal_basis: Mapped[bool] = mapped_column(Boolean, default=False)
    is_primary_operational_doc: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    family: Mapped['MeasureFamily'] = relationship(back_populates='documents')
    document: Mapped['NormalizedDocument'] = relationship(back_populates='family_links')


class ProfileFactCatalog(Base):
    __tablename__ = 'profile_fact_catalog'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    label: Mapped[str] = mapped_column(String(255))
    module: Mapped[str] = mapped_column(String(64), default=SurveyModule.CORE_ENTITY.value)
    value_kind: Mapped[str] = mapped_column(String(32), default=FactValueKind.SELECT.value)
    options: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    helper_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    why_needed: Mapped[str | None] = mapped_column(Text, nullable=True)
    stable: Mapped[bool] = mapped_column(Boolean, default=True)
    sensitive: Mapped[bool] = mapped_column(Boolean, default=False)
    required_in_core: Mapped[bool] = mapped_column(Boolean, default=False)
    depends_on: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    values: Mapped[list['ProfileFactValue']] = relationship(back_populates='fact')
    requirements: Mapped[list['MeasureFamilyRequirement']] = relationship(back_populates='fact')


class ProfileFactValue(Base):
    __tablename__ = 'profile_fact_values'
    __table_args__ = (UniqueConstraint('profile_id', 'fact_catalog_id', name='uq_profile_fact'),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    profile_id: Mapped[str] = mapped_column(ForeignKey('profiles.id'), index=True)
    fact_catalog_id: Mapped[str] = mapped_column(ForeignKey('profile_fact_catalog.id'), index=True)
    value_json: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    profile: Mapped['Profile'] = relationship(back_populates='fact_values')
    fact: Mapped['ProfileFactCatalog'] = relationship(back_populates='values')


class MeasureFamilyRequirement(Base):
    __tablename__ = 'measure_family_requirements'
    __table_args__ = (UniqueConstraint('measure_family_version_id', 'fact_catalog_id', name='uq_family_fact_requirement'),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    measure_family_version_id: Mapped[str] = mapped_column(ForeignKey('measure_family_versions.id'), index=True)
    fact_catalog_id: Mapped[str] = mapped_column(ForeignKey('profile_fact_catalog.id'), index=True)
    requirement_mode: Mapped[str] = mapped_column(String(64), default=RequirementMode.ENTITY_HARD_REQUIREMENT.value)
    expected_values: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    family_version: Mapped['MeasureFamilyVersion'] = relationship(back_populates='requirements')
    fact: Mapped['ProfileFactCatalog'] = relationship(back_populates='requirements')


class SurveyCoverageSnapshot(Base):
    __tablename__ = 'survey_coverage_snapshots'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    snapshot_key: Mapped[str] = mapped_column(String(128), index=True, default='latest')
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Opportunity(Base):
    __tablename__ = 'opportunities'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    current_version_id: Mapped[str | None] = mapped_column(ForeignKey('opportunity_versions.id'), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    short_description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(64))
    geography_scope: Mapped[str] = mapped_column(String(128), default='Italy')
    benefit_type: Mapped[str] = mapped_column(String(128))
    record_status: Mapped[str] = mapped_column(String(32), default=RecordStatus.PUBLISHED.value)
    verification_status: Mapped[str] = mapped_column(String(32), default=VerificationStatus.REVIEWED.value)
    deadline_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estimated_value_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    versions: Mapped[list['OpportunityVersion']] = relationship(
        back_populates='opportunity',
        foreign_keys='OpportunityVersion.opportunity_id',
    )
    current_version: Mapped['OpportunityVersion | None'] = relationship(
        foreign_keys=[current_version_id],
        post_update=True,
    )


class OpportunityVersion(Base):
    __tablename__ = 'opportunity_versions'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    opportunity_id: Mapped[str] = mapped_column(ForeignKey('opportunities.id'), index=True)
    source_snapshot_id: Mapped[str | None] = mapped_column(ForeignKey('source_snapshots.id'), nullable=True)
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    title: Mapped[str] = mapped_column(String(255))
    normalized_title: Mapped[str] = mapped_column(String(255))
    short_description: Mapped[str] = mapped_column(Text)
    long_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    opportunity_type: Mapped[str] = mapped_column(String(64))
    category: Mapped[str] = mapped_column(String(64))
    subcategory: Mapped[str | None] = mapped_column(String(64), nullable=True)
    issuer_name: Mapped[str] = mapped_column(String(255))
    issuer_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    country: Mapped[str] = mapped_column(String(2), default='IT')
    region: Mapped[str | None] = mapped_column(String(128), nullable=True)
    geography_scope: Mapped[str] = mapped_column(String(128))
    target_entities: Mapped[list[str]] = mapped_column(JSON)
    target_sectors: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    company_stage: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    company_size_constraints: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    demographic_constraints: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    legal_constraints: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    eligibility_inputs_required: Mapped[list[str]] = mapped_column(JSON)
    exclusions: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    benefit_type: Mapped[str] = mapped_column(String(128))
    benefit_value_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    estimated_value_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_value_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    funding_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    deadline_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    deadline_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    application_window_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    application_window_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    application_mode: Mapped[str | None] = mapped_column(String(128), nullable=True)
    required_documents: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    official_links: Mapped[list[str]] = mapped_column(JSON)
    source_documents: Mapped[list[str]] = mapped_column(JSON)
    evidence_snippets: Mapped[list[dict]] = mapped_column(JSON)
    extraction_confidence: Mapped[float] = mapped_column(Float, default=1.0)
    verification_status: Mapped[str] = mapped_column(String(32), default=VerificationStatus.REVIEWED.value)
    record_status: Mapped[str] = mapped_column(String(32), default=RecordStatus.PUBLISHED.value)
    changed_fields: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    opportunity: Mapped['Opportunity'] = relationship(
        back_populates='versions',
        foreign_keys=[opportunity_id],
    )
    rules: Mapped[list['OpportunityRule']] = relationship(back_populates='opportunity_version')


class OpportunityRule(Base):
    __tablename__ = 'opportunity_rules'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    opportunity_version_id: Mapped[str] = mapped_column(ForeignKey('opportunity_versions.id'), index=True)
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_json: Mapped[dict] = mapped_column(JSON)
    evidence_references: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    opportunity_version: Mapped['OpportunityVersion'] = relationship(back_populates='rules')
    test_cases: Mapped[list['RuleTestCase']] = relationship(back_populates='rule')


class RuleTestCase(Base):
    __tablename__ = 'rule_test_cases'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    rule_id: Mapped[str] = mapped_column(ForeignKey('opportunity_rules.id'), index=True)
    name: Mapped[str] = mapped_column(String(255))
    scenario_type: Mapped[str] = mapped_column(String(32))
    profile_payload: Mapped[dict] = mapped_column(JSON)
    expected_status: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    rule: Mapped['OpportunityRule'] = relationship(back_populates='test_cases')


class Match(Base):
    __tablename__ = 'matches'
    __table_args__ = (UniqueConstraint('user_id', 'opportunity_id', name='uq_match_user_opportunity'),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    opportunity_id: Mapped[str] = mapped_column(ForeignKey('opportunities.id'), index=True)
    match_status: Mapped[str] = mapped_column(String(32))
    match_score: Mapped[float] = mapped_column(Float, default=0)
    user_visible_reasoning: Mapped[str] = mapped_column(Text)
    explanation_summary: Mapped[str] = mapped_column(Text)
    missing_fields: Mapped[list[str]] = mapped_column(JSON)
    last_evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    evaluations: Mapped[list['MatchEvaluation']] = relationship(back_populates='match')


class MatchEvaluation(Base):
    __tablename__ = 'match_evaluations'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    match_id: Mapped[str] = mapped_column(ForeignKey('matches.id'), index=True)
    rule_id: Mapped[str | None] = mapped_column(ForeignKey('opportunity_rules.id'), nullable=True)
    rule_evaluation_trace: Mapped[dict] = mapped_column(JSON)
    ranking_inputs: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    match: Mapped['Match'] = relationship(back_populates='evaluations')


class SavedOpportunity(Base):
    __tablename__ = 'saved_opportunities'
    __table_args__ = (UniqueConstraint('user_id', 'opportunity_id', name='uq_saved_user_opportunity'),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    opportunity_id: Mapped[str] = mapped_column(ForeignKey('opportunities.id'), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ReviewItem(Base):
    __tablename__ = 'review_items'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    item_type: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default=ReviewStatus.OPEN.value)
    related_entity_type: Mapped[str] = mapped_column(String(64))
    related_entity_id: Mapped[str] = mapped_column(String(36), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class NotificationPreference(Base):
    __tablename__ = 'notification_preferences'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), unique=True, index=True)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    weekly_profile_nudges: Mapped[bool] = mapped_column(Boolean, default=True)
    deadline_reminders: Mapped[bool] = mapped_column(Boolean, default=True)
    new_opportunity_alerts: Mapped[bool] = mapped_column(Boolean, default=True)
    source_change_digests: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    user: Mapped['User'] = relationship(back_populates='notification_preferences')


class NotificationEvent(Base):
    __tablename__ = 'notification_events'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    opportunity_id: Mapped[str | None] = mapped_column(ForeignKey('opportunities.id'), nullable=True)
    dedupe_key: Mapped[str] = mapped_column(String(255), unique=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Notification(Base):
    __tablename__ = 'notifications'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    notification_event_id: Mapped[str] = mapped_column(ForeignKey('notification_events.id'), index=True)
    channel: Mapped[str] = mapped_column(String(32), default=NotificationChannel.EMAIL.value)
    status: Mapped[str] = mapped_column(String(32), default=NotificationStatus.PENDING.value)
    recipient: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AuditEvent(Base):
    __tablename__ = 'audit_events'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    action: Mapped[str] = mapped_column(String(128))
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[str] = mapped_column(String(36), index=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class IngestionRun(Base):
    __tablename__ = 'ingestion_runs'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    source_endpoint_id: Mapped[str] = mapped_column(ForeignKey('source_endpoints.id'), index=True)
    stage: Mapped[str] = mapped_column(String(32), default=IngestionStage.FETCH.value)
    status: Mapped[str] = mapped_column(String(32), default='queued')
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    diagnostics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
