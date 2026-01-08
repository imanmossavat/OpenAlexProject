from typing import Optional

from .venue_aliases import VenueAliasRepository
from .venue_cleaner import VenueCleaner
from .venue_fuzzy import VenueFuzzyMatcher


class VenueNormalizer:
  """Coordinates deterministic cleaning, alias lookup, and fuzzy fallback."""

  def __init__(
    self,
    cleaner: Optional[VenueCleaner] = None,
    alias_repository: Optional[VenueAliasRepository] = None,
    fuzzy_matcher: Optional[VenueFuzzyMatcher] = None,
  ) -> None:
    self._cleaner = cleaner or VenueCleaner()
    self._aliases = alias_repository or VenueAliasRepository()
    choices_provider = lambda: self._aliases.canonical_choices  # noqa: E731
    self._fuzzy = fuzzy_matcher or VenueFuzzyMatcher(choices_provider)

  def normalize(self, raw_value: Optional[str]) -> Optional[str]:
    if raw_value is None:
      return None
    cleaned = self._cleaner.clean(raw_value)
    if not cleaned:
      return raw_value.strip() or None

    alias = self._aliases.lookup(cleaned)
    if alias:
      return alias

    fuzzy = self._fuzzy.match(cleaned)
    if fuzzy:
      return fuzzy

    return cleaned.title()


_DEFAULT_NORMALIZER = VenueNormalizer()


def normalize_venue(raw_value: Optional[str]) -> Optional[str]:
  return _DEFAULT_NORMALIZER.normalize(raw_value)


def get_default_normalizer() -> VenueNormalizer:
  return _DEFAULT_NORMALIZER
