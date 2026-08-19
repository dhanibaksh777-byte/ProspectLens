from pydantic import BaseModel


class ProfileUpdate(BaseModel):
    website: str | None = None
    service_description: str | None = None
    ideal_customer_profile: str | None = None
    target_industries: list[str] = []
    keywords: list[str] = []
    company_size: str | None = None
    decision_maker_role: str | None = None
    target_countries: list[str] = []
    contact_preferences: dict = {}


class ProfileResponse(ProfileUpdate):
    class Config:
        from_attributes = True
