import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class SearchJobStatus(str, enum.Enum):
    queued = "queued"
    discovering = "discovering"
    enriching = "enriching"
    validating = "validating"
    deduping = "deduping"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class SearchJob(Base):
    __tablename__ = "search_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    name = Column(String, nullable=False)
    criteria_json = Column(JSON, nullable=False)  # full search criteria object from frontend

    status = Column(Enum(SearchJobStatus), default=SearchJobStatus.queued, nullable=False, index=True)
    progress = Column(Integer, default=0)  # 0-100
    leads_found = Column(Integer, default=0)
    duplicates_removed = Column(Integer, default=0)
    errors = Column(JSON, nullable=True)  # list of error strings, if any

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
