from pathlib import Path
from typing import TYPE_CHECKING
import logging

from .validation_models import ValidationResult, ValidationError

if TYPE_CHECKING:
    from ..models.library_inputs import LibraryCreationInputs
    from ..models.topic_modeling_inputs import TopicModelingInputs


class LibraryValidator:
    """Validates library-related inputs."""
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def validate_creation(self, inputs: 'LibraryCreationInputs') -> ValidationResult:
        """
        Validate library creation inputs.
        
        Args:
            inputs: Library creation inputs
            
        Returns:
            ValidationResult with any errors found
        """
        errors = []
        
        if not inputs.name or not inputs.name.strip():
            errors.append(ValidationError(
                field="name",
                message="Library name cannot be empty"
            ))
        
        if inputs.path.exists() and (inputs.path / "library_config.yaml").exists():
            errors.append(ValidationError(
                field="path",
                message=f"Library already exists at {inputs.path}",
                suggestion="Choose a different path or delete the existing library"
            ))
        
        if not inputs.paper_ids:
            errors.append(ValidationError(
                field="paper_ids",
                message="No papers selected",
                suggestion="Add papers from at least one source"
            ))
        
        valid_providers = ['openalex', 'semantic_scholar']
        if inputs.api_provider not in valid_providers:
            errors.append(ValidationError(
                field="api_provider",
                message=f"Invalid API provider: {inputs.api_provider}",
                suggestion=f"Choose from: {', '.join(valid_providers)}"
            ))
        
        return ValidationResult(errors=errors)
    
    def validate_topic_modeling(self, inputs: 'TopicModelingInputs') -> ValidationResult:
        """
        Validate topic modeling inputs.
        
        Args:
            inputs: Topic modeling inputs
            
        Returns:
            ValidationResult with any errors found
        """
        errors = []
        
        if not self._library_exists(inputs.library_path):
            errors.append(ValidationError(
                field="library_path",
                message=f"No library found at {inputs.library_path}",
                suggestion="Run 'crawler library-create' to create a library first"
            ))
        
        if inputs.model_type not in ['NMF', 'LDA']:
            errors.append(ValidationError(
                field="model_type",
                message=f"Invalid model type: {inputs.model_type}",
                suggestion="Choose 'NMF' or 'LDA'"
            ))
        
        if inputs.num_topics < 2:
            errors.append(ValidationError(
                field="num_topics",
                message=f"Number of topics must be at least 2, got {inputs.num_topics}",
                suggestion="Choose a value between 2 and 100"
            ))
        
        if inputs.num_topics > 100:
            errors.append(ValidationError(
                field="num_topics",
                message=f"Number of topics is too large: {inputs.num_topics}",
                suggestion="Choose a value between 2 and 100 for better results"
            ))
        
        return ValidationResult(errors=errors)
    
    def _library_exists(self, path: Path) -> bool:
        """Check if library exists at given path."""
        return (path / "library_config.yaml").exists()