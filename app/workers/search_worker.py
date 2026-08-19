"""
Runs as a FastAPI BackgroundTask — kicked off right after POST /api/searches
returns to the client. The client polls GET /api/searches/{id}/progress to
watch it move through statuses.

Provider selection: criteria_json can include "use_real_data": true to use
the Overpass provider instead of the mock one. Defaults to mock — real
scraping is opt-in since it's slower and depends on external services.
"""
from datetime import datetime, timezone

from app.database import SessionLocal
from app.models.search_job import SearchJob, SearchJobStatus
from app.models.lead import Lead, OutreachStatus
from app.services.providers import mock_provider, overpass_provider, tavily_provider
from app.services import scoring, validation


def run_search_job(search_job_id: str, user_id: str):
    db = SessionLocal()
    try:
        job = db.query(SearchJob).filter(SearchJob.id == search_job_id).first()
        if not job:
            return

        job.status = SearchJobStatus.discovering
        job.started_at = datetime.now(timezone.utc)
        job.progress = 10
        db.commit()

        # --- Discovery ---
        data_source = job.criteria_json.get("data_source", "mock")
        provider = {
            "mock": mock_provider,
            "overpass": overpass_provider,
            "tavily": tavily_provider,
        }.get(data_source, mock_provider)
        raw_leads = provider.discover(job.criteria_json)
        job.progress = 40
        db.commit()

        # --- Scoring + Validation ---
        job.status = SearchJobStatus.validating
        scored_leads = []
        for raw in raw_leads:
            score, reasons = scoring.score_lead(raw, job.criteria_json)
            scored_leads.append((raw, score, reasons))
        job.progress = 60
        db.commit()

        # --- Deduplication + Save ---
        job.status = SearchJobStatus.deduping
        saved_count = 0
        duplicate_count = 0

        for raw, score, reasons in scored_leads:
            website = raw.get("website_url")
            exists = False
            if website:
                exists = (
                    db.query(Lead)
                    .filter(Lead.user_id == user_id, Lead.website_url == website)
                    .first()
                    is not None
                )
            if exists:
                duplicate_count += 1
                continue

            lead = Lead(
                user_id=user_id,
                search_job_id=job.id,
                company_name=raw.get("company_name"),
                industry=raw.get("industry"),
                country=raw.get("country"),
                website_url=website,
                professional_email=raw.get("professional_email"),
                business_phone=raw.get("business_phone"),
                contact_name=raw.get("contact_name"),
                contact_role=raw.get("contact_role"),
                source_url=raw.get("source_url"),
                source_type=data_source if data_source != "mock" else "mock_provider",
                lead_score=score,
                match_reasons=reasons,
                email_status=validation.validate_email(raw.get("professional_email")),
                phone_status=validation.validate_phone(raw.get("business_phone")),
                outreach_status=OutreachStatus.new,
            )
            db.add(lead)
            saved_count += 1

        job.leads_found = saved_count
        job.duplicates_removed = duplicate_count
        job.progress = 100
        job.status = SearchJobStatus.completed
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as e:
        db.rollback()
        job = db.query(SearchJob).filter(SearchJob.id == search_job_id).first()
        if job:
            job.status = SearchJobStatus.failed
            job.errors = [str(e)]
            db.commit()
    finally:
        db.close()
