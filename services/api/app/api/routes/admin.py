from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_admin_user
from app.db.session import get_db
from app.models import IngestionRun, ReviewItem, Source
from app.schemas.common import ApiMessage
from app.schemas.corpus import AdminDocumentRead, BootstrapRunResult, MeasureFamilyRead, SurveyCoverageSnapshotRead
from app.schemas.review import ReviewItemRead, ReviewResolve, RuleTestResult
from app.schemas.source import IngestionRunRead, SourceCreate, SourceRead
from app.services.admin import (
    create_source,
    diff_opportunity,
    get_survey_coverage,
    list_document_payloads,
    list_measure_family_payloads,
    list_rules,
    publish_opportunity,
    resolve_review_item,
    run_bootstrap,
    test_rule,
    trigger_ingestion_run,
    unpublish_opportunity,
)
from app.services.notifications import run_deadline_reminders, run_weekly_digest

router = APIRouter(prefix='/v1/admin', tags=['admin'])


@router.get('/sources', response_model=list[SourceRead])
def get_sources(db: Session = Depends(get_db), _=Depends(get_admin_user)) -> list[SourceRead]:
    items = db.execute(select(Source).order_by(Source.created_at.desc())).scalars().all()
    return [SourceRead.model_validate(item) for item in items]


@router.get('/measure-families', response_model=list[MeasureFamilyRead])
def get_measure_families(db: Session = Depends(get_db), _=Depends(get_admin_user)) -> list[MeasureFamilyRead]:
    return [MeasureFamilyRead.model_validate(item) for item in list_measure_family_payloads(db)]


@router.get('/documents', response_model=list[AdminDocumentRead])
def get_documents(
    source_domain: str | None = None,
    role: str | None = None,
    lifecycle_status: str | None = None,
    family_slug: str | None = None,
    db: Session = Depends(get_db),
    _=Depends(get_admin_user),
) -> list[AdminDocumentRead]:
    items = list_document_payloads(
        db,
        source_domain=source_domain,
        role=role,
        lifecycle_status=lifecycle_status,
        family_slug=family_slug,
    )
    return [AdminDocumentRead.model_validate(item) for item in items]


@router.get('/survey/coverage', response_model=SurveyCoverageSnapshotRead)
def get_admin_survey_coverage(db: Session = Depends(get_db), _=Depends(get_admin_user)) -> SurveyCoverageSnapshotRead:
    return SurveyCoverageSnapshotRead.model_validate(get_survey_coverage(db))


@router.post('/bootstrap/run', response_model=BootstrapRunResult)
def post_bootstrap_run(db: Session = Depends(get_db), _=Depends(get_admin_user)) -> BootstrapRunResult:
    return BootstrapRunResult.model_validate(run_bootstrap(db))


@router.post('/sources', response_model=SourceRead)
def post_source(payload: SourceCreate, db: Session = Depends(get_db), _=Depends(get_admin_user)) -> SourceRead:
    source = create_source(db, payload)
    return SourceRead.model_validate(source)


@router.post('/sources/{source_id}/run', response_model=IngestionRunRead)
def post_source_run(source_id: str, db: Session = Depends(get_db), _=Depends(get_admin_user)) -> IngestionRunRead:
    run = trigger_ingestion_run(db, source_id)
    if run is None:
        raise HTTPException(status_code=404, detail='Source or endpoint not found')
    return IngestionRunRead.model_validate(run)


@router.get('/ingestion-runs', response_model=list[IngestionRunRead])
def get_ingestion_runs(db: Session = Depends(get_db), _=Depends(get_admin_user)) -> list[IngestionRunRead]:
    items = db.execute(select(IngestionRun).order_by(IngestionRun.started_at.desc())).scalars().all()
    return [IngestionRunRead.model_validate(item) for item in items]


@router.get('/review-items', response_model=list[ReviewItemRead])
def get_review_items(db: Session = Depends(get_db), _=Depends(get_admin_user)) -> list[ReviewItemRead]:
    items = db.execute(select(ReviewItem).order_by(ReviewItem.created_at.desc())).scalars().all()
    return [ReviewItemRead.model_validate(item) for item in items]


@router.post('/review-items/{review_item_id}/resolve', response_model=ReviewItemRead)
def post_resolve_review_item(review_item_id: str, payload: ReviewResolve, db: Session = Depends(get_db), user=Depends(get_admin_user)) -> ReviewItemRead:
    item = resolve_review_item(db, review_item_id, payload.resolution_note, user.id)
    if item is None:
        raise HTTPException(status_code=404, detail='Review item not found')
    return ReviewItemRead.model_validate(item)


@router.get('/opportunities/{opportunity_id}/diff')
def get_opportunity_diff(opportunity_id: str, db: Session = Depends(get_db), _=Depends(get_admin_user)) -> dict:
    diff = diff_opportunity(db, opportunity_id)
    if diff is None:
        raise HTTPException(status_code=404, detail='Opportunity not found')
    return diff


@router.post('/opportunities/{opportunity_id}/publish', response_model=ApiMessage)
def post_publish_opportunity(opportunity_id: str, db: Session = Depends(get_db), user=Depends(get_admin_user)) -> ApiMessage:
    opportunity = publish_opportunity(db, opportunity_id, user.id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail='Opportunity not found')
    return ApiMessage(message='Opportunity published')


@router.post('/opportunities/{opportunity_id}/unpublish', response_model=ApiMessage)
def post_unpublish_opportunity(opportunity_id: str, db: Session = Depends(get_db), user=Depends(get_admin_user)) -> ApiMessage:
    opportunity = unpublish_opportunity(db, opportunity_id, user.id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail='Opportunity not found')
    return ApiMessage(message='Opportunity unpublished')


@router.post('/rules/{rule_id}/test', response_model=RuleTestResult)
def post_rule_test(rule_id: str, db: Session = Depends(get_db), _=Depends(get_admin_user)) -> RuleTestResult:
    result = test_rule(db, rule_id)
    if result is None:
        raise HTTPException(status_code=404, detail='Rule not found')
    return RuleTestResult.model_validate(result)


@router.get('/rules')
def get_rules(db: Session = Depends(get_db), _=Depends(get_admin_user)) -> list[dict]:
    return list_rules(db)


@router.post('/notifications/run-reminders', response_model=ApiMessage)
def post_run_deadline_reminders(db: Session = Depends(get_db), _=Depends(get_admin_user)) -> ApiMessage:
    count = run_deadline_reminders(db)
    return ApiMessage(message=f'Deadline reminder emails dispatched: {count}')


@router.post('/notifications/run-digest', response_model=ApiMessage)
def post_run_weekly_digest(db: Session = Depends(get_db), _=Depends(get_admin_user)) -> ApiMessage:
    count = run_weekly_digest(db)
    return ApiMessage(message=f'Weekly digest emails dispatched: {count}')
