from pydantic import BaseModel


class CoverageStats(BaseModel):
    with_website: int
    with_phone: int
    with_professional_email: int


class GroupCount(BaseModel):
    name: str
    count: int


class PipelineStage(BaseModel):
    stage: str
    count: int


class DashboardStats(BaseModel):
    cards: dict
    coverage: CoverageStats
    by_country: list[GroupCount]
    by_industry: list[GroupCount]
    pipeline: list[PipelineStage]
