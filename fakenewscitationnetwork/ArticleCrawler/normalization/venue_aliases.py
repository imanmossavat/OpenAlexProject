import json
from pathlib import Path
from typing import Dict, Optional


class VenueAliasRepository:
  """Loads venue alias definitions and exposes lookup helpers."""

  def __init__(self, alias_file: Optional[Path] = None) -> None:
    if alias_file:
      self._alias_file = alias_file
    else:
      # Prefer repo-level data/venues.json; fall back to package-local path.
      repo_root = Path(__file__).resolve().parents[2]
      repo_data = repo_root / "data" / "venues.json"
      package_data = Path(__file__).resolve().parents[1] / "data" / "venues.json"
      self._alias_file = repo_data if repo_data.exists() else package_data
    self._alias_map: Dict[str, str] = {}
    self._choices: Optional[list[str]] = None
    self.reload()

  def reload(self) -> None:
    """Load alias map from disk."""
    if not self._alias_file.exists():
      self._alias_map = {}
      self._choices = None
      return
    content = self._alias_file.read_text(encoding="utf-8")
    data = json.loads(content or "{}")
    # store lowercase keys for consistent lookup
    self._alias_map = {k.lower(): v for k, v in data.items()}
    self._choices = list({value for value in self._alias_map.values()})

  def lookup(self, key: Optional[str]) -> Optional[str]:
    if not key:
      return None
    return self._alias_map.get(key.lower())

  @property
  def canonical_choices(self) -> list[str]:
    if self._choices is None:
      self._choices = list({value for value in self._alias_map.values()})
    return self._choices
