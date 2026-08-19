import uuid

from sqlalchemy import Column, String, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base

# Many-to-many join table: one lead can have many tags, one tag can be on many leads.
lead_tag_associations = Table(
    "lead_tag_associations",
    Base.metadata,
    Column("lead_id", UUID(as_uuid=True), ForeignKey("leads.id"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("lead_tags.id"), primary_key=True),
)


class LeadTag(Base):
    __tablename__ = "lead_tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)

    leads = relationship("Lead", secondary=lead_tag_associations, back_populates="tags")
