from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

@dataclass
class LibraryCreationInputs:
    """Input data for library creation."""
    name: str
    path: Path
    description: Optional[str]
    paper_ids: List[str]
    api_provider: str = 'openalex'
    
    def __post_init__(self):
        """Ensure path is a Path object."""
        if not isinstance(self.path, Path):
            self.path = Path(self.path)