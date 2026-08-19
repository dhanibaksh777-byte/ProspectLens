import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)

    website = Column(String, nullable=True)
    service_description = Column(String, nullable=True)
    ideal_customer_profile = Column(String, nullable=True)
    target_industries = Column(JSON, default=list)  # e.g. ["Software", "IT Services"]
    keywords = Column(JSON, default=list)            # e.g. ["Python", "React"]
    company_size = Column(String, nullable=True)
    decision_maker_role = Column(String, nullable=True)
    target_countries = Column(JSON, default=list)     # e.g. ["Pakistan", "India"]
    contact_preferences = Column(JSON, default=dict)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
