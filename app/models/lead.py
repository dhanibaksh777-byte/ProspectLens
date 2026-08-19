import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, JSON, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.lead_tag import lead_tag_associations


class EmailStatus(str, enum.Enum):
    unknown = "unknown"
    syntax_valid = "syntax_valid"
    domain_valid = "domain_valid"
    deliverable = "deliverable"
    risky = "risky"
    invalid = "invalid"


class PhoneStatus(str, enum.Enum):
    unknown = "unknown"
    normalized = "normalized"
    valid = "valid"
    invalid = "invalid"


class WhatsAppStatus(str, enum.Enum):
    unknown = "unknown"
    link_found = "link_found"
    likely = "likely"
    verified = "verified"
    not_available = "not_available"


class OutreachStatus(str, enum.Enum):
    new = "new"
    pending_outreach = "pending_outreach"
    contacted = "contacted"
    replied = "replied"
    qualified = "qualified"
    not_interested = "not_interested"
    invalid = "invalid"
    duplicate = "duplicate"
    suppressed = "suppressed"


class Lead(Base):
    __tablename__ = "leads"
    __table_args__ = (
        # Prevents the same website being saved twice for the same user.
        UniqueConstraint("user_id", "website_url", name="uq_user_website"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    search_job_id = Column(UUID(as_uuid=True), ForeignKey("search_jobs.id"), nullable=True)

    company_name = Column(String, nullable=False)
    industry = Column(String, nullable=True)
    country = Column(String, nullable=True)
    website_url = Column(String, nullable=True)

    professional_email = Column(String, nullable=True)
    personal_email = Column(String, nullable=True)
    business_phone = Column(String, nullable=True)
    whatsapp_status = Column(Enum(WhatsAppStatus), default=WhatsAppStatus.unknown)

    contact_name = Column(String, nullable=True)
    contact_role = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)

    source_url = Column(String, nullable=True)
    source_type = Column(String, nullable=True)  # e.g. "website", "manual"

    email_status = Column(Enum(EmailStatus), default=EmailStatus.unknown)
    phone_status = Column(Enum(PhoneStatus), default=PhoneStatus.unknown)

    lead_score = Column(Integer, default=0)
    match_reasons = Column(JSON, default=list)
    website_observations = Column(JSON, default=list)

    outreach_status = Column(Enum(OutreachStatus), default=OutreachStatus.new, nullable=False, index=True)

    discovered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    tags = relationship("LeadTag", secondary=lead_tag_associations, back_populates="leads")
