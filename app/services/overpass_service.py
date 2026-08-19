"""
Discovers businesses using OpenStreetMap's free Overpass API.

Flow:
1. Geocode the area name to a bounding box (via Nominatim, also free).
2. Query Overpass for business nodes within that box matching the category.
3. Return raw business dicts (name, category, area, phone, website).

No API key needed. Data completeness varies since it relies on what's
tagged in OpenStreetMap, which is why enrichment_service exists to fill
in emails from business websites afterward.
"""
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Maps a human category (what the user types) to OSM tag keys/values worth checking.
# OSM doesn't have one clean tag for "needs visual design" so we search across
# multiple tag groups (shop, amenity, office) that commonly match.
CATEGORY_TAG_MAP = {
    "restaurant": ['node["amenity"="restaurant"]'],
    "cafe": ['node["amenity"="cafe"]'],
    "salon": ['node["shop"="hairdresser"]', 'node["shop"="beauty"]'],
    "real estate": ['node["office"="estate_agent"]'],
    "retail": ['node["shop"]'],
    "gym": ['node["leisure"="fitness_centre"]'],
    "clinic": ['node["amenity"="clinic"]', 'node["amenity"="doctors"]'],
    "hotel": ['node["tourism"="hotel"]'],
    "software house": ['node["office"="it"]', 'node["office"="coworking"]'],
    "it": ['node["office"="it"]', 'node["office"="coworking"]'],
    "office": ['node["office"]'],
}


def geocode_area(area_name: str):
    """Returns (south, west, north, east) bounding box for the given area name."""
    resp = requests.get(
        NOMINATIM_URL,
        params={"q": area_name, "format": "json", "limit": 1},
        headers={"User-Agent": "ProspectLens/1.0"},
        timeout=15,
    )
    resp.raise_for_status()
    results = resp.json()
    if not results:
        raise ValueError(f"Could not find location for area: {area_name}")

    bbox = results[0]["boundingbox"]  # [south, north, west, east] as strings
    south, north, west, east = (float(x) for x in bbox)
    return south, west, north, east


def build_overpass_query(category: str, bbox: tuple) -> str:
    south, west, north, east = bbox
    box_str = f"{south},{west},{north},{east}"

    tag_filters = CATEGORY_TAG_MAP.get(category.lower())
    if not tag_filters:
        # Fallback: generic shop/office/amenity search for unmapped categories.
        tag_filters = ['node["shop"]', 'node["office"]', 'node["amenity"]']

    node_queries = "\n".join(f'  {tf}({box_str});' for tf in tag_filters)
    return f"""
    [out:json][timeout:25];
    (
    {node_queries}
    );
    out body;
    """


def discover_businesses(area_name: str, category: str, limit: int = 30):
    bbox = geocode_area(area_name)
    query = build_overpass_query(category, bbox)

    resp = requests.post(
        OVERPASS_URL,
        data={"data": query},
        headers={"User-Agent": "ProspectLens/1.0"},
        timeout=30,
    )
    if not resp.ok:
        raise ValueError(f"Overpass API error ({resp.status_code}): {resp.text[:300]}")
    elements = resp.json().get("elements", [])

    businesses = []
    for el in elements[:limit]:
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue  # skip unnamed nodes, not useful as leads

        businesses.append({
            "business_name": name,
            "category": category,
            "area": area_name,
            "phone": tags.get("phone") or tags.get("contact:phone"),
            "website_url": tags.get("website") or tags.get("contact:website"),
        })

    return businesses
