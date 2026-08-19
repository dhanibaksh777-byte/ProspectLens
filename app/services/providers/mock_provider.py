"""
Generates fake-but-structured leads for testing the search pipeline before
a real provider (Overpass, Phase 5) is wired in. Data is clearly synthetic —
not meant to look like real scraped businesses, just enough shape to
exercise the full flow: discover -> save -> list -> filter.
"""
import random

from app.services.providers.base import RawLead, SearchCriteria

NAME_PREFIXES = ["Apex", "Bright", "Prime", "North Star", "Blue Ridge", "Summit", "Crescent"]
NAME_SUFFIXES = ["Solutions", "Group", "Studio", "Labs", "Partners", "Works"]

CONTACT_ROLES = ["CEO", "Founder", "Operations Manager", "Marketing Head"]
CONTACT_NAMES = ["Sara Ahmed", "Bilal Khan", "Zara Malik", "Usman Raza", "Ayesha Tariq"]


def _fake_company_name() -> str:
    return f"{random.choice(NAME_PREFIXES)} {random.choice(NAME_SUFFIXES)}"


def discover(criteria: SearchCriteria) -> list[RawLead]:
    industries = criteria.get("industries") or ["General"]
    countries = criteria.get("countries") or ["Pakistan"]
    max_leads = criteria.get("maximum_leads") or 10

    leads: list[RawLead] = []
    for i in range(max_leads):
        name = _fake_company_name()
        domain = name.lower().replace(" ", "") + ".example.com"

        leads.append(RawLead(
            company_name=name,
            industry=random.choice(industries),
            country=random.choice(countries),
            website_url=f"https://{domain}",
            professional_email=f"contact@{domain}",
            business_phone=f"+92300{random.randint(1000000, 9999999)}",
            contact_name=random.choice(CONTACT_NAMES),
            contact_role=random.choice(CONTACT_ROLES),
            source_url=f"https://{domain}/about",
        ))

    return leads
