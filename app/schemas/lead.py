import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.lead import EmailStatus, PhoneStatus, WhatsAppStatus, OutreachStatus


# ---- Lead read/update shapes ----

class LeadResponse(BaseModel):
    id: uuid.UUID
    company_name: str
    industry: str | None
    country: str | None
    website_url: str | None
    professional_email: str | None
    personal_email: str | None
    business_phone: str | None
    whatsapp_status: WhatsAppStatus
    contact_name: str | None
    contact_role: str | None
    linkedin_url: str | None
    source_url: str | None
    source_type: str | None
    email_status: EmailStatus
    phone_status: PhoneStatus
    lead_score: int
    match_reasons: list[str]
    website_observations: list[str]
    outreach_status: OutreachStatus
    discovered_at: datetime
    last_verified_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class LeadUpdate(BaseModel):
    """General field edits — NOT for outreach_status, use the /status endpoint for that."""
    company_name: str | None = None
    industry: str | None = None
    country: str | None = None
    website_url: str | None = None
    professional_email: str | None = None
    personal_email: str | None = None
    business_phone: str | None = None
    contact_name: str | None = None
    contact_role: str | None = None
    linkedin_url: str | None = None


class LeadStatusUpdate(BaseModel):
    outreach_status: OutreachStatus


class LeadCreate(BaseModel):
    """Manually add a lead (not from a scrape)."""
    company_name: str
    industry: str | None = None
    country: str | None = None
    website_url: str | None = None
    professional_email: str | None = None
    business_phone: str | None = None
    contact_name: str | None = None
    contact_role: str | None = None
    linkedin_url: str | None = None


# ---- Notes ----

class LeadNoteCreate(BaseModel):
    content: str


class LeadNoteResponse(BaseModel):
    id: uuid.UUID
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Activity ----

class ActivityEventResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    from_value: str | None
    to_value: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Scraper (Overpass discovery) ----

class ScrapeRequest(BaseModel):
    area: str        # city/country name passed to Overpass, stored as Lead.country
    category: str
    limit: int = 30


class ScrapeResponse(BaseModel):
    total_found: int
    total_saved: int
    leads: list[LeadResponse]


# ---- Tags ----

class TagCreate(BaseModel):
    name: str


class TagResponse(BaseModel):
    id: uuid.UUID
    name: str

    class Config:
        from_attributes = True
