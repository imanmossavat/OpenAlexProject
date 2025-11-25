from typing import Optional

try:
  from rapidfuzz import fuzz, process
except ImportError:  # pragma: no cover - handled gracefully without dependency
  fuzz = None
  process = None


class VenueFuzzyMatcher:
  """Fuzzy fallback matching using RapidFuzz when available."""

  def __init__(self, choices_provider) -> None:
    """
    Args:
      choices_provider: Callable returning iterable of canonical venue names.
    """
    self._choices_provider = choices_provider

  def match(self, cleaned_value: Optional[str], threshold: int = 90) -> Optional[str]:
    if not cleaned_value or not process or not fuzz:
      return None
    choices = list(self._choices_provider())
    if not choices:
      return None
    match = process.extractOne(
      cleaned_value,
      choices,
      scorer=fuzz.WRatio,
    )
    if not match:
      return None
    candidate, score, _ = match
    return candidate if score >= threshold else None
