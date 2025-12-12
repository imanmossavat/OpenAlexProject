from typing import Optional


def normalize_openalex_id(value: Optional[str]) -> Optional[str]:
    """Return normalized OpenAlex ID (e.g., W123) if present."""
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    if "openalex.org" in raw:
        raw = raw.split("/")[-1]
    raw = raw.strip()
    if not raw:
        return None
    if raw[0].lower() == "w":
        suffix = raw[1:]
        if suffix.isdigit():
            return f"W{suffix}"
    return None


def normalize_doi(value: Optional[str]) -> Optional[str]:
    """Return DOI stripped of protocol/prefix."""
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    raw = raw.replace("https://doi.org/", "").replace("http://doi.org/", "")
    raw = raw.replace("DOI:", "").replace("doi:", "")
    raw = raw.strip()
    if raw.startswith("10."):
        return raw
    return None


def extract_doi_from_url(url: Optional[str]) -> Optional[str]:
    """Pull DOI out of a URL if it contains doi.org."""
    if not url:
        return None
    if "doi.org/" in url:
        parts = url.split("doi.org/")
        if len(parts) > 1:
            doi = parts[1].split("?")[0]
            return doi.strip()
    return None
