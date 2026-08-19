"""
Wraps the existing Overpass discovery + email enrichment services to match
the LeadProvider Protocol (same discover() signature as mock_provider).
This is what makes the search_worker able to swap providers with one line.
"""
from app.services import overpass_service, enrichment_service
from app.services.providers.base import RawLead, SearchCriteria


def discover(criteria: SearchCriteria) -> list[RawLead]:
    countries = criteria.get("countries") or ["Pakistan"]
    industries = criteria.get("industries") or ["restaurant"]
    max_leads = criteria.get("maximum_leads") or 10

    # Overpass needs one area + one category per call, so we loop combos
    # and split the requested max_leads roughly evenly across them.
    per_combo_limit = max(1, max_leads // (len(countries) * len(industries)))

    raw_leads: list[RawLead] = []
    for country in countries:
        for industry in industries:
            try:
                businesses = overpass_service.discover_businesses(
                    area_name=country, category=industry, limit=per_combo_limit
                )
            except ValueError:
                continue  # bad area name for this combo, skip it, don't fail the whole search

            for business in businesses:
                business = enrichment_service.enrich_lead(business)
                raw_leads.append(RawLead(
                    company_name=business["business_name"],
                    industry=industry,
                    country=country,
                    website_url=business.get("website_url"),
                    professional_email=business.get("email"),
                    business_phone=business.get("phone"),
                    source_url=business.get("website_url"),
                ))

            if len(raw_leads) >= max_leads:
                return raw_leads[:max_leads]

    return raw_leads
