"""
User prompting abstraction layer.

Provides interface for user interaction that can be swapped out
for different UI implementations (CLI, GUI, web, etc.).
"""

from abc import ABC, abstractmethod
from typing import Optional
import questionary
from questionary import Style
from rich.console import Console


class Prompter(ABC):
    """
    Abstract interface for user interaction.
    
    This abstraction allows swapping UI implementations without
    changing command logic (Dependency Inversion Principle).
    """
    
    @abstractmethod
    def input(self, prompt: str, default: str = "") -> str:
        """Get text input from user."""
        pass
    
    @abstractmethod
    def input_int(self, prompt: str, default: int = 0, min_value: int = None, max_value: int = None) -> int:
        """Get integer input from user with validation."""
        pass
    
    @abstractmethod
    def confirm(self, message: str, default: bool = False) -> bool:
        """Get yes/no confirmation from user."""
        pass
    
    @abstractmethod
    def choice(self, message: str, choices: list[str], default: int = 0) -> int:
        """Present choices and return selected index."""
        pass
    
    @abstractmethod
    def error(self, message: str):
        """Display error message."""
        pass
    
    @abstractmethod
    def success(self, message: str):
        """Display success message."""
        pass
    
    @abstractmethod
    def warning(self, message: str):
        """Display warning message."""
        pass


class RichPrompter(Prompter):
    """
    Rich/Questionary implementation of Prompter.
    
    Provides beautiful terminal prompts with validation.
    """
    
    def __init__(self, console: Console = None):
        self.console = console or Console()
        
        # Custom style for prompts
        self.style = Style([
            ('question', 'fg:#00ffff bold'),
            ('answer', 'fg:#00ff00 bold'),
            ('pointer', 'fg:#00ffff bold'),
            ('selected', 'fg:#00ff00'),
            ('separator', 'fg:#666666'),
        ])
    
    def input(self, prompt: str, default: str = "") -> str:
        """Get text input from user."""
        result = questionary.text(
            prompt + ":",
            default=default,
            style=self.style
        ).ask()
        
        return result if result is not None else ""
    
    def input_int(self, prompt: str, default: int = 0, min_value: int = None, max_value: int = None) -> int:
        """Get integer input with validation."""
        while True:
            result = questionary.text(
                f"{prompt} [{default}]:",
                default=str(default),
                style=self.style
            ).ask()
            
            if result is None:
                return default
            
            try:
                value = int(result)
                
                if min_value is not None and value < min_value:
                    self.error(f"Value must be at least {min_value}")
                    continue
                
                if max_value is not None and value > max_value:
                    self.error(f"Value must be at most {max_value}")
                    continue
                
                return value
                
            except ValueError:
                self.error(f"Please enter a valid integer")
    
    def confirm(self, message: str, default: bool = False) -> bool:
        """Get yes/no confirmation."""
        result = questionary.confirm(
            message,
            default=default,
            style=self.style
        ).ask()
        
        return result if result is not None else default
    
    def checkbox(self, message: str, choices: list[str]) -> list[str]:
        from questionary import checkbox
        
        result = checkbox(
            message,
            choices=[{"name": choice, "value": choice} for choice in choices]
        ).ask()
        
        return result if result else []
    
    def choice(self, message: str, choices: list[str], default: int = 0) -> int:
        """Present choices and return selected index."""
        result = questionary.select(
            message + ":",
            choices=choices,
            default=choices[default] if default < len(choices) else choices[0],
            style=self.style
        ).ask()
        
        if result is None:
            return default
        
        return choices.index(result)
    
    def error(self, message: str):
        """Display error message."""
        self.console.print(f"[bold red]❌ {message}[/bold red]")
    
    def success(self, message: str):
        """Display success message."""
        self.console.print(f"[bold green]✓ {message}[/bold green]")
    
    def warning(self, message: str):
        """Display warning message."""
        self.console.print(f"[bold yellow]⚠️  {message}[/bold yellow]")


class SimplePrompter(Prompter):
    """
    Simple fallback implementation using built-in input().
    
    Used when Rich/Questionary are not available.
    """
    
    def input(self, prompt: str, default: str = "") -> str:
        """Get text input from user."""
        user_input = input(f"{prompt} [{default}]: " if default else f"{prompt}: ")
        return user_input if user_input else default
    
    def input_int(self, prompt: str, default: int = 0, min_value: int = None, max_value: int = None) -> int:
        """Get integer input with validation."""
        while True:
            try:
                user_input = input(f"{prompt} [{default}]: ")
                value = int(user_input) if user_input else default
                
                if min_value is not None and value < min_value:
                    print(f"Error: Value must be at least {min_value}")
                    continue
                
                if max_value is not None and value > max_value:
                    print(f"Error: Value must be at most {max_value}")
                    continue
                
                return value
                
            except ValueError:
                print("Error: Please enter a valid integer")
    
    def confirm(self, message: str, default: bool = False) -> bool:
        """Get yes/no confirmation."""
        default_str = "Y/n" if default else "y/N"
        user_input = input(f"{message} ({default_str}): ").lower()
        
        if not user_input:
            return default
        
        return user_input in ['y', 'yes']
    
    def choice(self, message: str, choices: list[str], default: int = 0) -> int:
        """Present choices and return selected index."""
        print(f"\n{message}:")
        for idx, choice in enumerate(choices):
            marker = ">" if idx == default else " "
            print(f"{marker} {idx + 1}) {choice}")
        
        while True:
            try:
                user_input = input(f"\nChoice [1-{len(choices)}] [{default + 1}]: ")
                if not user_input:
                    return default
                
                choice_num = int(user_input)
                if 1 <= choice_num <= len(choices):
                    return choice_num - 1
                else:
                    print(f"Error: Please enter a number between 1 and {len(choices)}")
            except ValueError:
                print("Error: Please enter a valid number")

    
    
    def error(self, message: str):
        """Display error message."""
        print(f"❌ {message}")
    
    def success(self, message: str):
        """Display success message."""
        print(f"✓ {message}")
    
    def warning(self, message: str):
        """Display warning message."""
        print(f"⚠️  {message}")