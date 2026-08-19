"""
A LeadProvider is anything that can take search criteria and return raw
leads. This Protocol is the contract — mock_provider.py implements it now,
and overpass_provider.py (Phase 5) will implement it the same way. The
search worker doesn't care which one it's talking to.
"""
from typing import Protocol, TypedDict


class RawLead(TypedDict, total=False):
    company_name: str
    industry: str
    country: str
    website_url: str
    professional_email: str
    business_phone: str
    contact_name: str
    contact_role: str
    linkedin_url: str
    source_url: str


class SearchCriteria(TypedDict, total=False):
    industries: list[str]
    keywords: list[str]
    countries: list[str]
    company_size: str
    decision_maker_role: str
    maximum_leads: int


class LeadProvider(Protocol):
    def discover(self, criteria: SearchCriteria) -> list[RawLead]:
        ...
