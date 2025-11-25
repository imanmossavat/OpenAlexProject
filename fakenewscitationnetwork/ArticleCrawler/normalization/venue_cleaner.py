import re
from typing import Optional


class VenueCleaner:
  """Apply deterministic cleanup rules before alias or fuzzy matching."""

  # compile regex patterns once
  _PUBLISHER_PREFIX = re.compile(r'^(springer|elsevier|acm|mdpi|ieee)\s*[:\-]\s*', re.IGNORECASE)
  _LEADING_YEAR = re.compile(r'^\d{4}\s+')
  _TRAILING_YEAR = re.compile(r'\s+\d{4}$')
  _PROCEEDINGS = re.compile(r'^(in:|proceedings of|proc\.?)\s+', re.IGNORECASE)
  _VOLUME_TOKEN = re.compile(r'\(?\d+\s*\(\d+\)\)?')
  _PAGES_TOKEN = re.compile(r'(pp\.?|pages)\s*\d+(\s*[-–]\s*\d+)?', re.IGNORECASE)
  _PARENS = re.compile(r'\(.*?\)')
  _ALNUM_SPACE = re.compile(r'[^a-z0-9\s]')
  _WHITESPACE = re.compile(r'\s+')

  def clean(self, raw_value: Optional[str]) -> str:
    if not raw_value:
      return ""

    value = raw_value.strip().lower()
    value = self._PUBLISHER_PREFIX.sub("", value)
    value = self._LEADING_YEAR.sub("", value)
    value = self._TRAILING_YEAR.sub("", value)
    value = self._PROCEEDINGS.sub("", value)
    value = self._VOLUME_TOKEN.sub(" ", value)
    value = self._PAGES_TOKEN.sub(" ", value)
    value = self._PARENS.sub(" ", value)
    value = self._ALNUM_SPACE.sub(" ", value)
    value = self._WHITESPACE.sub(" ", value)
    return value.strip()
