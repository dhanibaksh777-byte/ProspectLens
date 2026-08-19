"""
Syntax-level validation for emails and phones. Deterministic — no AI, no
external API calls (that would be a Phase 6+ upgrade, e.g. a deliverability
checker). This just confirms the data LOOKS like a valid email/phone.
"""
import re

from app.models.lead import EmailStatus, PhoneStatus

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
PHONE_REGEX = re.compile(r"^\+?[0-9\s\-()]{7,20}$")


def validate_email(email: str | None) -> EmailStatus:
    if not email:
        return EmailStatus.unknown
    if EMAIL_REGEX.match(email.strip()):
        return EmailStatus.syntax_valid
    return EmailStatus.invalid


def validate_phone(phone: str | None) -> PhoneStatus:
    if not phone:
        return PhoneStatus.unknown
    if PHONE_REGEX.match(phone.strip()):
        return PhoneStatus.normalized
    return PhoneStatus.invalid
