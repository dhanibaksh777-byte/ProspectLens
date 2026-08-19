from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.lead import Lead, OutreachStatus
from app.models.lead_note import LeadNote
from app.models.lead_tag import LeadTag
from app.models.activity import ActivityEvent
from app.models.suppression import SuppressionEntry, SuppressionType
from app.schemas.lead import (
    ScrapeRequest, ScrapeResponse, LeadResponse, LeadUpdate, LeadCreate,
    LeadStatusUpdate, LeadNoteCreate, LeadNoteResponse, ActivityEventResponse,
    TagCreate, TagResponse,
)
from app.schemas.ai import MatchExplanationResponse, OutreachDraftRequest, OutreachDraftResponse
from app.services import overpass_service, enrichment_service
from app.services.ai import match_explanation, outreach_draft

router = APIRouter()


def _get_owned_lead(lead_id: str, user: User, db: Session) -> Lead:
    """Fetches a lead only if it belongs to the current user — prevents
    one user from reading/editing another user's leads by guessing an id."""
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.user_id == user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


# ---- Discovery (Overpass scrape) ----

@router.post("/scrape", response_model=ScrapeResponse)
def scrape_leads(
    payload: ScrapeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        businesses = overpass_service.discover_businesses(
            area_name=payload.area, category=payload.category, limit=payload.limit
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    saved_leads = []
    for business in businesses:
        business = enrichment_service.enrich_lead(business)

        website = business.get("website_url")
        existing = None
        if website:
            existing = (
                db.query(Lead)
                .filter(Lead.user_id == current_user.id, Lead.website_url == website)
                .first()
            )
        if existing:
            continue

        lead = Lead(
            user_id=current_user.id,
            company_name=business["business_name"],
            industry=business.get("category"),
            country=business.get("area"),
            website_url=website,
            professional_email=business.get("email"),
            business_phone=business.get("phone"),
            source_type="scraped",
            outreach_status=OutreachStatus.new,
        )
        db.add(lead)
        saved_leads.append(lead)

    db.commit()
    for lead in saved_leads:
        db.refresh(lead)

    return ScrapeResponse(
        total_found=len(businesses),
        total_saved=len(saved_leads),
        leads=saved_leads,
    )


# ---- CRUD ----

@router.get("", response_model=list[LeadResponse])
def list_leads(
    outreach_status: OutreachStatus | None = None,
    country: str | None = None,
    industry: str | None = None,
    minimum_score: int | None = None,
    search: str | None = Query(None, description="Matches against company name"),
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Lead).filter(Lead.user_id == current_user.id)

    if outreach_status:
        query = query.filter(Lead.outreach_status == outreach_status)
    if country:
        query = query.filter(Lead.country == country)
    if industry:
        query = query.filter(Lead.industry == industry)
    if minimum_score is not None:
        query = query.filter(Lead.lead_score >= minimum_score)
    if search:
        query = query.filter(or_(Lead.company_name.ilike(f"%{search}%")))

    return query.order_by(Lead.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get_owned_lead(lead_id, current_user, db)


@router.post("", response_model=LeadResponse, status_code=201)
def create_lead(
    payload: LeadCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = Lead(user_id=current_user.id, source_type="manual", **payload.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.patch("/{lead_id}", response_model=LeadResponse)
def update_lead(
    lead_id: str,
    payload: LeadUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = _get_owned_lead(lead_id, current_user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)
    db.commit()
    db.refresh(lead)
    return lead


@router.delete("/{lead_id}", status_code=204)
def delete_lead(lead_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    lead = _get_owned_lead(lead_id, current_user, db)
    db.delete(lead)
    db.commit()


# ---- Status changes (always logged as an activity event) ----

@router.post("/{lead_id}/status", response_model=LeadResponse)
def update_status(
    lead_id: str,
    payload: LeadStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = _get_owned_lead(lead_id, current_user, db)
    old_status = lead.outreach_status
    lead.outreach_status = payload.outreach_status

    db.add(ActivityEvent(
        lead_id=lead.id,
        user_id=current_user.id,
        event_type="status_changed",
        from_value=old_status.value,
        to_value=payload.outreach_status.value,
    ))
    db.commit()
    db.refresh(lead)
    return lead


# ---- Notes ----

@router.post("/{lead_id}/notes", response_model=LeadNoteResponse, status_code=201)
def add_note(
    lead_id: str,
    payload: LeadNoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = _get_owned_lead(lead_id, current_user, db)
    note = LeadNote(lead_id=lead.id, user_id=current_user.id, content=payload.content)
    db.add(note)
    db.add(ActivityEvent(
        lead_id=lead.id, user_id=current_user.id, event_type="note_added",
    ))
    db.commit()
    db.refresh(note)
    return note


# ---- Tags ----

@router.post("/{lead_id}/tags", response_model=TagResponse, status_code=201)
def add_tag(
    lead_id: str,
    payload: TagCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = _get_owned_lead(lead_id, current_user, db)

    tag = db.query(LeadTag).filter(LeadTag.user_id == current_user.id, LeadTag.name == payload.name).first()
    if not tag:
        tag = LeadTag(user_id=current_user.id, name=payload.name)
        db.add(tag)
        db.flush()  # get tag.id before using it below

    if tag not in lead.tags:
        lead.tags.append(tag)
        db.add(ActivityEvent(
            lead_id=lead.id, user_id=current_user.id, event_type="tag_added", to_value=tag.name,
        ))

    db.commit()
    db.refresh(tag)
    return tag


@router.get("/{lead_id}/tags", response_model=list[TagResponse])
def list_tags(lead_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    lead = _get_owned_lead(lead_id, current_user, db)
    return lead.tags


@router.delete("/{lead_id}/tags/{tag_id}", status_code=204)
def remove_tag(
    lead_id: str, tag_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = _get_owned_lead(lead_id, current_user, db)
    tag = db.query(LeadTag).filter(LeadTag.id == tag_id, LeadTag.user_id == current_user.id).first()
    if tag and tag in lead.tags:
        lead.tags.remove(tag)
        db.commit()


# ---- Suppression ----

@router.post("/{lead_id}/suppress", response_model=LeadResponse)
def suppress_lead(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = _get_owned_lead(lead_id, current_user, db)

    value = lead.professional_email or lead.business_phone or lead.website_url
    if value:
        db.add(SuppressionEntry(
            user_id=current_user.id,
            value=value,
            suppression_type=SuppressionType.email if lead.professional_email else SuppressionType.phone,
            reason="Manually suppressed via lead",
        ))

    old_status = lead.outreach_status
    lead.outreach_status = OutreachStatus.suppressed
    db.add(ActivityEvent(
        lead_id=lead.id, user_id=current_user.id, event_type="status_changed",
        from_value=old_status.value, to_value="suppressed",
    ))
    db.commit()
    db.refresh(lead)
    return lead


# ---- Activity timeline ----

@router.get("/{lead_id}/activity", response_model=list[ActivityEventResponse])
def get_activity(lead_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_owned_lead(lead_id, current_user, db)  # ownership check
    return (
        db.query(ActivityEvent)
        .filter(ActivityEvent.lead_id == lead_id)
        .order_by(ActivityEvent.created_at.desc())
        .all()
    )


# ---- AI features (Phase 7) — explanation and drafting only, never invents facts ----

@router.post("/{lead_id}/explain-match", response_model=MatchExplanationResponse)
def explain_match_endpoint(
    lead_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = _get_owned_lead(lead_id, current_user, db)
    lead_dict = LeadResponse.model_validate(lead).model_dump()
    explanation = match_explanation.explain_match(lead_dict)
    return MatchExplanationResponse(explanation=explanation)


@router.post("/{lead_id}/draft-outreach", response_model=OutreachDraftResponse)
def draft_outreach_endpoint(
    lead_id: str,
    payload: OutreachDraftRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = _get_owned_lead(lead_id, current_user, db)
    lead_dict = LeadResponse.model_validate(lead).model_dump()
    draft = outreach_draft.draft_outreach(lead_dict, channel=payload.channel)
    return OutreachDraftResponse(draft=draft, channel=payload.channel)
