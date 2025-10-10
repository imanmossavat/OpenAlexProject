from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm
import questionary

from ..models.topic_modeling_inputs import TopicModelingInputs


class TopicModelingInputCollector:
    """Collects inputs for topic modeling."""
    
    def __init__(self, console: Console):
        self.console = console
    
    def collect(
        self,
        library_path: Optional[str] = None,
        model_type: Optional[str] = None,
        num_topics: Optional[int] = None
    ) -> Optional[TopicModelingInputs]:
        """
        Collect all required inputs for topic modeling.
        
        Args:
            library_path: Path to library (prompts if None)
            model_type: Model type (prompts if None)
            num_topics: Number of topics (prompts if None)
            
        Returns:
            TopicModelingInputs or None if cancelled
        """
        if not library_path:
            library_path = self._ask_library_path()
            if not library_path:
                return None
        
        if not model_type:
            model_type = self._ask_model_type()
            if not model_type:
                return None
        
        if not num_topics:
            num_topics = self._ask_num_topics()
            if num_topics is None:
                return None
        
        inputs = TopicModelingInputs(
            library_path=Path(library_path),
            model_type=model_type,
            num_topics=num_topics
        )
        
        if not self._confirm_inputs(inputs):
            return None
        
        return inputs
    
    def _ask_library_path(self) -> Optional[str]:
        """Ask user for library path."""
        choice = self._ask_library_choice()
        
        if choice == "create":
            self.console.print("\n[cyan]Let's create a new library first...[/cyan]\n")
            return "CREATE_NEW"
        
        return Prompt.ask("Enter library path")
    
    def _ask_library_choice(self) -> str:
        """Ask if user wants existing library or to create new one."""
        choice = questionary.select(
            "Do you want to:",
            choices=[
                questionary.Choice("Use an existing library", value="existing"),
                questionary.Choice("Create a new library", value="create")
            ]
        ).ask()
        
        return choice if choice else "existing"
    
    def _ask_model_type(self) -> Optional[str]:
        """Ask user for model type."""
        return questionary.select(
            "Select topic modeling algorithm:",
            choices=[
                questionary.Choice("NMF (Non-negative Matrix Factorization)", value="NMF"),
                questionary.Choice("LDA (Latent Dirichlet Allocation)", value="LDA")
            ]
        ).ask()
    
    def _ask_num_topics(self) -> Optional[int]:
        """Ask user for number of topics."""
        num_str = Prompt.ask("Number of topics", default="5")
        try:
            return int(num_str)
        except ValueError:
            self.console.print("[red]Invalid number[/red]")
            return None
    
    def _confirm_inputs(self, inputs: TopicModelingInputs) -> bool:
        """Display configuration and ask for confirmation."""
        self.console.print("\n[bold]Configuration:[/bold]")
        self.console.print(f"  Library: {inputs.library_path}")
        self.console.print(f"  Algorithm: {inputs.model_type}")
        self.console.print(f"  Topics: {inputs.num_topics}")
        
        return Confirm.ask("\nProceed with topic modeling?")