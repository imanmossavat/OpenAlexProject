import re
from typing import List

SPLIT_PATTERN = re.compile(r"(?:,|;|\\\\|\band\b|\n)", flags=re.IGNORECASE)


def parse_author_list(raw_text: str) -> List[str]:
    """Normalize author lists split by commas, semicolons, 'and', '\\\\', or new lines."""
    if not raw_text:
        return []

    parts = SPLIT_PATTERN.split(raw_text)
    return [part.strip() for part in parts if part and part.strip()]
