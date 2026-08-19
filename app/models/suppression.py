import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class SuppressionType(str, enum.Enum):
    email = "email"
    domain = "domain"
    phone = "phone"


class SuppressionEntry(Base):
    __tablename__ = "suppression_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    value = Column(String, nullable=False, index=True)  # the email/domain/phone being suppressed
    suppression_type = Column(Enum(SuppressionType), nullable=False)
    reason = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
