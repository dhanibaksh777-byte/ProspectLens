"""
Drafts a cold outreach message (email or WhatsApp) using only real lead
data. The AI writes the message TEXT — it never invents the recipient's
email/phone/name; those come straight from the Lead record, and if a
field is missing, the prompt explicitly tells the model not to reference it.
"""
from app.services.ai.groq_client import generate

SYSTEM_PROMPT = (
    "You are writing a short, professional cold outreach message on behalf "
    "of a visual design service, reaching out to a business that may need "
    "design help. Use ONLY the facts given about the business — never "
    "invent a contact name, past interaction, or detail not provided. If no "
    "contact name is given, use a generic greeting like 'Hi there'. Keep it "
    "under 80 words, friendly, no hard sell, end with a soft call to action."
)


def draft_outreach(lead: dict, channel: str = "email") -> str:
    facts = (
        f"Business name: {lead.get('company_name')}\n"
        f"Industry: {lead.get('industry') or 'unknown'}\n"
        f"Contact name: {lead.get('contact_name') or 'not available — use generic greeting'}\n"
        f"Channel: {channel} (adjust tone/length: email can be slightly longer, "
        f"WhatsApp should be shorter and more casual)"
    )
    return generate(SYSTEM_PROMPT, facts, max_tokens=400)
