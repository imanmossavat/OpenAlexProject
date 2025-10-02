"""
Input validation utilities.
"""

from pathlib import Path
import re


def validate_paper_id(paper_id: str) -> bool:
    """
    Validate paper ID format.
    
    Accepts various formats:
    - W123456789 (OpenAlex)
    - 1234567890abcdef12345678 (Semantic Scholar)
    - DOI formats
    
    Args:
        paper_id: Paper ID string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not paper_id or not paper_id.strip():
        return False
    
    paper_id = paper_id.strip()
    
    # OpenAlex format: W followed by digits
    if re.match(r'^W\d+$', paper_id):
        return True
    
    # Semantic Scholar format: hexadecimal string
    if re.match(r'^[0-9a-fA-F]{24,40}$', paper_id):
        return True
    
    # Allow DOI format as well
    if 'doi.org' in paper_id.lower() or paper_id.startswith('10.'):
        return True
    
    return False


def validate_file_path(path: str) -> tuple[bool, str]:
    """
    Validate file path and check if file exists.
    
    Args:
        path: File path string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path or not path.strip():
        return False, "Path cannot be empty"
    
    try:
        file_path = Path(path).expanduser().resolve()
        
        if not file_path.exists():
            return False, f"File does not exist: {file_path}"
        
        if not file_path.is_file():
            return False, f"Path is not a file: {file_path}"
        
        return True, ""
        
    except Exception as e:
        return False, f"Invalid path: {e}"


def validate_experiment_name(name: str) -> tuple[bool, str]:
    """
    Validate experiment name.
    
    Args:
        name: Experiment name string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, "Name cannot be empty"
    
    # Check for invalid characters
    if not re.match(r'^[a-zA-Z0-9_\-\s]+$', name):
        return False, "Name can only contain letters, numbers, spaces, hyphens, and underscores"
    
    # Check length
    if len(name) > 100:
        return False, "Name is too long (max 100 characters)"
    
    return True, ""