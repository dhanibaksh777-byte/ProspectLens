"""
Uses Tavily's search API (free tier, no card, 1000 searches/month) to find
real businesses on the live web -- much better coverage than Overpass for
B2B/office businesses (software houses, agencies, startups) that don't
register themselves on OpenStreetMap.

Flow: search query per industry+country combo -> get real company websites
-> reuse enrichment_service to pull an email off each website, same as the
Overpass provider does.
"""
import re

import requests

from app.config import settings
from app.services import enrichment_service
from app.services.providers.base import RawLead, SearchCriteria

TAVILY_URL = "https://api.tavily.com/search"

# Titles/domains that are clearly not a real company (directories, social
# media, job boards) -- skip these so we don't save junk "leads".
JUNK_DOMAINS = [
    "linkedin.com", "facebook.com", "youtube.com", "wikipedia.org",
    "indeed.com", "glassdoor.com", "instagram.com", "twitter.com", "x.com",
    "scribd.com", "designrush.com", "clutch.co", "goodfirms.co",
    "upcity.com", "sortlist.com", "topdevelopers.co", "medium.com",
    "reddit.com", "quora.com", "pinterest.com",
]

# Titles matching these patterns are "best of" listicles/directories, not
# a single real company -- skip them even if the domain itself looks fine.
LISTICLE_TITLE_PATTERNS = re.compile(
    r"\b(top \d+|best \d+|\d+ (top|best)|list of|companies in|list\b)", re.IGNORECASE
)


def _clean_company_name(title: str) -> str:
    # Search result titles are often "Company Name - Home" or "Company | Services"
    # Strip common separators and trailing site-nav text.
    name = re.split(r"[-|:]", title)[0].strip()
    return name[:100]  # keep it sane length


def discover(criteria: SearchCriteria) -> list[RawLead]:
    if not settings.tavily_api_key:
        raise RuntimeError("tavily_api_key is not set in .env — get a free key at tavily.com")

    industries = criteria.get("industries") or ["software house"]
    countries = criteria.get("countries") or ["Pakistan"]
    max_leads = criteria.get("maximum_leads") or 10
    per_query_limit = max(3, max_leads // (len(industries) * len(countries)))

    raw_leads: list[RawLead] = []
    seen_domains = set()
    last_error = None

    for industry in industries:
        for country in countries:
            query = f'"{industry}" company official website Pakistan {country} -list -top -best'
            try:
                resp = requests.post(
                    TAVILY_URL,
                    headers={
                        "Authorization": f"Bearer {settings.tavily_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "query": query,
                        "max_results": per_query_limit,
                        "search_depth": "basic",
                    },
                    timeout=20,
                )
                if not resp.ok:
                    last_error = f"Tavily error ({resp.status_code}): {resp.text[:200]}"
                    continue
                results = resp.json().get("results", [])
            except requests.RequestException as e:
                last_error = str(e)
                continue

            for r in results:
                url = r.get("url", "")
                domain = url.split("//")[-1].split("/")[0].replace("www.", "")

                if any(junk in domain for junk in JUNK_DOMAINS):
                    continue
                if LISTICLE_TITLE_PATTERNS.search(r.get("title", "")):
                    continue  # "Top 10 Software Companies..." is an article, not a company
                if domain in seen_domains:
                    continue
                seen_domains.add(domain)

                business = {"website_url": url}
                business = enrichment_service.enrich_lead(business)

                raw_leads.append(RawLead(
                    company_name=_clean_company_name(r.get("title", domain)),
                    industry=industry,
                    country=country,
                    website_url=url,
                    professional_email=business.get("email"),
                    source_url=url,
                ))

                if len(raw_leads) >= max_leads:
                    return raw_leads[:max_leads]

    if not raw_leads and last_error:
        raise ValueError(f"Tavily search failed for all queries. Last error: {last_error}")

    return raw_leads
