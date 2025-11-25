import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
  sys.path.append(str(PROJECT_ROOT))

from ArticleCrawler.normalization.venue_aliases import VenueAliasRepository
from ArticleCrawler.normalization.venue_normalizer import VenueNormalizer


def build_normalizer(tmp_path, aliases):
  alias_file = tmp_path / "venues.json"
  alias_file.write_text(json.dumps(aliases))
  repository = VenueAliasRepository(alias_file=alias_file)
  return VenueNormalizer(alias_repository=repository)


def test_normalizer_applies_alias_after_cleaning(tmp_path):
  normalizer = build_normalizer(
    tmp_path,
    {"2nd international test conference": "TESTCONF"},
  )

  assert (
    normalizer.normalize("2022 2nd International Test Conference (ITC)")
    == "TESTCONF"
  )


def test_normalizer_fallback_title_cases_cleaned_value(tmp_path):
  normalizer = build_normalizer(tmp_path, {})

  value = normalizer.normalize("2020 example workshop!!!")
  assert value == "Example Workshop"
