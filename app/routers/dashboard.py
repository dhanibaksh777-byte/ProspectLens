import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.lead import Lead, OutreachStatus
from app.schemas.dashboard import DashboardStats, CoverageStats, GroupCount, PipelineStage

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
def get_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    base = db.query(Lead).filter(Lead.user_id == current_user.id)

    total = base.count()
    avg_score = db.query(func.avg(Lead.lead_score)).filter(Lead.user_id == current_user.id).scalar() or 0

    cards = {
        "total_leads": total,
        "new_leads": base.filter(Lead.outreach_status == OutreachStatus.new).count(),
        "pending_outreach": base.filter(Lead.outreach_status == OutreachStatus.pending_outreach).count(),
        "contacted": base.filter(Lead.outreach_status == OutreachStatus.contacted).count(),
        "replied": base.filter(Lead.outreach_status == OutreachStatus.replied).count(),
        "qualified": base.filter(Lead.outreach_status == OutreachStatus.qualified).count(),
        "average_score": round(float(avg_score), 1),
    }

    coverage = CoverageStats(
        with_website=base.filter(Lead.website_url.isnot(None)).count(),
        with_phone=base.filter(Lead.business_phone.isnot(None)).count(),
        with_professional_email=base.filter(Lead.professional_email.isnot(None)).count(),
    )

    by_country_raw = (
        db.query(Lead.country, func.count(Lead.id))
        .filter(Lead.user_id == current_user.id, Lead.country.isnot(None))
        .group_by(Lead.country)
        .order_by(func.count(Lead.id).desc())
        .limit(10)
        .all()
    )
    by_country = [GroupCount(name=row[0], count=row[1]) for row in by_country_raw]

    by_industry_raw = (
        db.query(Lead.industry, func.count(Lead.id))
        .filter(Lead.user_id == current_user.id, Lead.industry.isnot(None))
        .group_by(Lead.industry)
        .order_by(func.count(Lead.id).desc())
        .limit(10)
        .all()
    )
    by_industry = [GroupCount(name=row[0], count=row[1]) for row in by_industry_raw]

    pipeline = [
        PipelineStage(stage=status.value, count=base.filter(Lead.outreach_status == status).count())
        for status in OutreachStatus
    ]

    return DashboardStats(cards=cards, coverage=coverage, by_country=by_country, by_industry=by_industry, pipeline=pipeline)


@router.post("/export")
def export_leads(
    outreach_status: OutreachStatus | None = None,
    country: str | None = None,
    industry: str | None = None,
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

    leads = query.order_by(Lead.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "company_name", "industry", "country", "website_url",
        "professional_email", "business_phone", "contact_name",
        "contact_role", "outreach_status", "lead_score", "created_at"
    ])
    for lead in leads:
        writer.writerow([
            lead.company_name, lead.industry, lead.country, lead.website_url,
            lead.professional_email, lead.business_phone, lead.contact_name,
            lead.contact_role, lead.outreach_status.value, lead.lead_score,
            lead.created_at.isoformat()
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads_export.csv"}
    )
