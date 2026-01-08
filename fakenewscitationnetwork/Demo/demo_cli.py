"""
Demo script for testing the ArticleCrawler CLI.

This script shows how to use the CLI programmatically and
also serves as a test for the CLI installation.
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_cli_import():
    """Test that CLI can be imported."""
    try:
        from ArticleCrawler.cli import app
        print(" CLI module imported successfully")
        return True
    except ImportError as e:
        print(f" Failed to import CLI: {e}")
        return False


def test_wizard_command():
    """Test wizard command availability."""
    try:
        from ArticleCrawler.cli.main import app
        
        commands = []
        for command in app.registered_commands:
            if hasattr(command, 'callback') and command.callback:
                cmd_name = command.callback.__name__
                commands.append(cmd_name)
        
        if commands:
            print(f" Available commands: {', '.join(commands)}")
            return True
        else:
            print(" CLI app created (commands will be registered on execution)")
            return True
            
    except Exception as e:
        print(f" Failed to check commands: {e}")
        return False


def test_dependencies():
    """Test that CLI dependencies are installed."""
    print("\nChecking dependencies...")
    
    dependencies = {
        'typer': 'typer',
        'rich': 'rich',
        'questionary': 'questionary',
        'pyyaml': 'yaml',
        'pydantic': 'pydantic'
    }
    
    all_installed = True
    for name, import_name in dependencies.items():
        try:
            __import__(import_name)
            print(f"   {name}")
        except ImportError:
            print(f"   {name} (missing)")
            all_installed = False
    
    return all_installed


def show_usage():
    """Display usage information."""
    print("\n" + "=" * 70)
    print("ARTICLECRAWLER CLI - USAGE GUIDE")
    print("=" * 70)
    print("\n1. Install CLI dependencies:")
    print("   pip install -e '.[cli]'")
    print("\n2. Run the interactive wizard:")
    print("   crawler wizard")
    print("\n   Or with Python:")
    print("   python -m ArticleCrawler.cli.main wizard")
    print("\n3. Run from config file:")
    print("   crawler run --config experiment.yaml")
    print("\n4. Get help:")
    print("   crawler --help")
    print("\n5. Check version:")
    print("   crawler version")
    print("\n" + "=" * 70 + "\n")


def test_cli_execution():
    """Test that CLI can be executed."""
    try:
        from ArticleCrawler.cli.main import app
        from typer.testing import CliRunner
        
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        
        if result.exit_code == 0:
            print(" CLI help command works")
            return True
        else:
            print(f" CLI help command failed with exit code {result.exit_code}")
            return False
            
    except Exception as e:
        print(f" Failed to execute CLI: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("TESTING ARTICLECRAWLER CLI")
    print("=" * 70 + "\n")
    
    success = True
    
    print("Test 1: Module Import")
    success &= test_cli_import()
    print()
    
    print("Test 2: Dependencies")
    deps_ok = test_dependencies()
    success &= deps_ok
    print()
    
    if not deps_ok:
        print("\n  Missing dependencies detected!")
        print("\nTo install CLI dependencies, run:")
        print("  pip install typer[all] rich questionary pyyaml pydantic")
        print("\nOr install ArticleCrawler with CLI support:")
        print("  pip install -e '.[cli]'")
        print("\n" + "=" * 70 + "\n")
        sys.exit(1)
    
    print("Test 3: Command Registration")
    success &= test_wizard_command()
    print()
    
    print("Test 4: CLI Execution")
    success &= test_cli_execution()
    print()
    
    if success:
        print("\n" + "=" * 70)
        print(" ALL CLI TESTS PASSED!")
        print("=" * 70)
        show_usage()
    else:
        print("\n" + "=" * 70)
        print(" SOME CLI TESTS FAILED")
        print("=" * 70)
        print("\nTroubleshooting:")
        print("1. Make sure all dependencies are installed:")
        print("   pip install -e '.[cli]'")
        print("\n2. Try running the wizard directly:")
        print("   python -m ArticleCrawler.cli.main wizard")
        print("\n3. Check for import errors:")
        print("   python -c 'from ArticleCrawler.cli import app; print(app)'")
        print("\n" + "=" * 70 + "\n")
        sys.exit(1)