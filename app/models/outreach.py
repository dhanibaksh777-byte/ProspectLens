import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Channel(str, enum.Enum):
    email = "email"
    whatsapp = "whatsapp"


class Direction(str, enum.Enum):
    outbound = "outbound"
    inbound = "inbound"


class OutreachMessage(Base):
    __tablename__ = "outreach_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    channel = Column(Enum(Channel), nullable=False)
    direction = Column(Enum(Direction), nullable=False)
    content = Column(Text, nullable=False)
    ai_generated = Column(Boolean, default=False)
    intent_classification = Column(String, nullable=True)  # interested / not_interested / question / neutral
    sent_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
