from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ValidationError:
    """Represents a validation error."""
    field: str
    message: str
    suggestion: Optional[str] = None
    
    def __str__(self) -> str:
        """Format error for display."""
        msg = f"{self.field}: {self.message}"
        if self.suggestion:
            msg += f"\n  Suggestion: {self.suggestion}"
        return msg


@dataclass
class ValidationResult:
    """Result of validation."""
    errors: List[ValidationError]
    
    @property
    def is_valid(self) -> bool:
        """Check if validation passed."""
        return len(self.errors) == 0
    
    def get_error_messages(self) -> List[str]:
        """Get all error messages."""
        return [str(error) for error in self.errors]