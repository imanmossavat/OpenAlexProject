import re
from typing import Optional


DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")


def find_doi(text: str) -> Optional[str]:
    """Return DOI string when one is present in the text."""
    if not text:
        return None
    match = DOI_PATTERN.search(text)
    return match.group(0) if match else None
