from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_optional_current_user
from app.db.session import get_db
from app.schemas.common import ApiMessage
from app.schemas.opportunity import OpportunityCard, OpportunityDetail
from app.services.opportunities import (
    get_opportunity_detail,
    interpret_query,
    list_opportunities,
    save_opportunity,
    unsave_opportunity,
)

router = APIRouter(prefix='/v1', tags=['opportunities'])


@router.get('/opportunities', response_model=list[OpportunityCard])
def get_opportunities(
    query: str | None = Query(default=None),
    category: str | None = Query(default=None),
    matched_status: str | None = Query(default=None),
    saved_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    user=Depends(get_optional_current_user),
) -> list[OpportunityCard]:
    items = list_opportunities(db, user, query=query, category=category, matched_status=matched_status, saved_only=saved_only)
    return [OpportunityCard.model_validate(item) for item in items]


@router.get('/opportunities/{opportunity_key}', response_model=OpportunityDetail)
def get_opportunity(opportunity_key: str, db: Session = Depends(get_db), user=Depends(get_optional_current_user)) -> OpportunityDetail:
    detail = get_opportunity_detail(db, opportunity_key, user)
    if detail is None:
        raise HTTPException(status_code=404, detail='Opportunity not found')
    return OpportunityDetail.model_validate(detail)


@router.post('/opportunities/{opportunity_id}/save', response_model=ApiMessage)
def post_save(opportunity_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)) -> ApiMessage:
    save_opportunity(db, user, opportunity_id)
    return ApiMessage(message='Opportunity saved')


@router.delete('/opportunities/{opportunity_id}/save', response_model=ApiMessage)
def delete_save(opportunity_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)) -> ApiMessage:
    unsave_opportunity(db, user, opportunity_id)
    return ApiMessage(message='Opportunity removed from saved list')


@router.get('/search', response_model=list[OpportunityCard])
def search(
    query: str = Query(...),
    db: Session = Depends(get_db),
    user=Depends(get_optional_current_user),
) -> list[OpportunityCard]:
    parsed = interpret_query(query)
    items = list_opportunities(db, user, query=parsed['query'], category=parsed['category'])
    return [OpportunityCard.model_validate(item) for item in items]
