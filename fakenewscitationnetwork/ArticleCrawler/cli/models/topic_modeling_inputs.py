from dataclasses import dataclass
from pathlib import Path

@dataclass
class TopicModelingInputs:
    """Input data for topic modeling."""
    library_path: Path
    model_type: str
    num_topics: int
    
    def __post_init__(self):
        """Ensure path is a Path object and model_type is uppercase."""
        if not isinstance(self.library_path, Path):
            self.library_path = Path(self.library_path)
        self.model_type = self.model_type.upper()