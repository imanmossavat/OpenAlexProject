from rich.console import Console
from typing import List

from ..validators.validation_models import ValidationResult


class ErrorFormatter:
    """Formats validation and other errors for display."""
    
    @staticmethod
    def display_validation_errors(result: ValidationResult, console: Console) -> None:
        """
        Display validation errors in a user-friendly format.
        
        Args:
            result: Validation result with errors
            console: Rich console for output
        """
        if result.is_valid:
            return
        
        console.print("\n[bold red]❌ Validation Errors:[/bold red]\n")
        
        for error in result.errors:
            console.print(f"[red]• {error.field}:[/red] {error.message}")
            if error.suggestion:
                console.print(f"  [yellow]→ {error.suggestion}[/yellow]")
        
        console.print()