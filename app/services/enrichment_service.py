"""
Enriches a lead's data by visiting its website and pulling an email address.

Most small business sites either put an email directly in text/footer or
behind a mailto: link. We check both. This is a best-effort pass — many
sites will yield nothing, which is expected and fine (see LeadScraper flow).
"""
import re

import requests
from bs4 import BeautifulSoup

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# Generic addresses we skip in favor of a more specific one if found later.
LOW_PRIORITY_PREFIXES = ("noreply", "no-reply", "webmaster", "postmaster")


def extract_email_from_website(website_url: str) -> str | None:
    if not website_url:
        return None

    url = website_url if website_url.startswith("http") else f"https://{website_url}"

    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
    except requests.RequestException:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # 1. Check mailto: links first, most reliable signal.
    for link in soup.select('a[href^="mailto:"]'):
        email = link["href"].replace("mailto:", "").split("?")[0].strip()
        if email and not email.lower().startswith(LOW_PRIORITY_PREFIXES):
            return email

    # 2. Fallback: regex over visible page text (catches "Email: foo@bar.com").
    matches = EMAIL_REGEX.findall(soup.get_text())
    good_matches = [m for m in matches if not m.lower().startswith(LOW_PRIORITY_PREFIXES)]
    if good_matches:
        return good_matches[0]

    return matches[0] if matches else None


def enrich_lead(business: dict) -> dict:
    """Takes a business dict from overpass_service and adds an email if found."""
    email = extract_email_from_website(business.get("website_url"))
    business["email"] = email
    return business
