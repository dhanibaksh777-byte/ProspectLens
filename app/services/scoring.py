"""
Deterministic lead scoring — no AI here on purpose. Points are added for
signals that make a lead more usable/valuable. Simple, explainable, fast.
"""
from app.services.providers.base import RawLead, SearchCriteria


def score_lead(raw: RawLead, criteria: SearchCriteria) -> tuple[int, list[str]]:
    """Returns (score 0-100, list of match_reasons strings)."""
    score = 0
    reasons = []

    if raw.get("website_url"):
        score += 20
        reasons.append("Has a website")

    if raw.get("professional_email"):
        score += 30
        reasons.append("Professional email found")

    if raw.get("business_phone"):
        score += 20
        reasons.append("Phone number available")

    if raw.get("contact_name"):
        score += 15
        reasons.append("Named contact identified")

    target_industries = [i.lower() for i in criteria.get("industries", [])]
    if raw.get("industry", "").lower() in target_industries:
        score += 10
        reasons.append("Target industry match")

    target_countries = [c.lower() for c in criteria.get("countries", [])]
    if raw.get("country", "").lower() in target_countries:
        score += 5
        reasons.append("Target country match")

    return min(score, 100), reasons
