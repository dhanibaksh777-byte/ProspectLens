"""
Turns the already-computed, deterministic match_reasons + lead_score into a
short natural-language paragraph. The AI does NOT decide the score or
reasons — those come from scoring.py (deterministic). This only explains
them in plain language, so it can never invent new "reasons" that aren't
grounded in real data.
"""
from app.services.ai.groq_client import generate

SYSTEM_PROMPT = (
    "You are a sales assistant explaining why a business lead is a good fit "
    "for outreach. You will be given real, verified facts about the lead "
    "and a match score. Write a 2-3 sentence explanation using ONLY the "
    "facts given — never invent contact details, company history, or facts "
    "not provided. Be concise and business-like."
)


def explain_match(lead: dict) -> str:
    facts = (
        f"Company: {lead.get('company_name')}\n"
        f"Industry: {lead.get('industry') or 'unknown'}\n"
        f"Country: {lead.get('country') or 'unknown'}\n"
        f"Has website: {bool(lead.get('website_url'))}\n"
        f"Has professional email: {bool(lead.get('professional_email'))}\n"
        f"Has phone: {bool(lead.get('business_phone'))}\n"
        f"Match score: {lead.get('lead_score')}/100\n"
        f"Match reasons (deterministic): {', '.join(lead.get('match_reasons', [])) or 'none'}"
    )
    return generate(SYSTEM_PROMPT, facts, max_tokens=300)
