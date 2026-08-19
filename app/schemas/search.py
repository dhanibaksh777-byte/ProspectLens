import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.search_job import SearchJobStatus


class SearchCriteriaInput(BaseModel):
    industries: list[str] = []
    keywords: list[str] = []
    countries: list[str] = []
    company_size: str | None = None
    decision_maker_role: str | None = None
    maximum_leads: int = 10
    data_source: str = "mock"  # "mock" | "overpass" (free, physical businesses) | "tavily" (free, web-wide, better for B2B)


class SearchJobCreate(BaseModel):
    name: str
    criteria: SearchCriteriaInput


class SearchJobResponse(BaseModel):
    id: uuid.UUID
    name: str
    criteria_json: dict
    status: SearchJobStatus
    progress: int
    leads_found: int
    duplicates_removed: int
    errors: list[str] | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class SearchProgressResponse(BaseModel):
    status: SearchJobStatus
    progress: int
    leads_found: int
