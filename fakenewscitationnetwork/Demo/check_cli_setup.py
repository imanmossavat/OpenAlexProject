"""
Quick CLI setup checker.

Run this first to verify your environment is ready for the CLI.
"""

import sys
from pathlib import Path

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f" Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f" Python {version.major}.{version.minor}.{version.micro} (need 3.8+)")
        return False


def check_dependencies():
    """Check if CLI dependencies are installed."""
    print("\nChecking CLI dependencies:")
    
    required = {
        'typer': 'CLI framework',
        'rich': 'Terminal formatting',
        'questionary': 'Interactive prompts',
        'yaml': 'YAML configuration (pyyaml)',
        'pydantic': 'Data validation'
    }
    
    missing = []
    
    for module, description in required.items():
        try:
            __import__(module)
            print(f"   {module:15} - {description}")
        except ImportError:
            print(f"   {module:15} - {description} [MISSING]")
            missing.append(module)
    
    return missing


def check_articlecrawler():
    """Check if ArticleCrawler can be imported."""
    print("\nChecking ArticleCrawler:")
    try:
        import ArticleCrawler
        print(f"   ArticleCrawler found")
        
        # Check if CLI module exists
        cli_path = Path(ArticleCrawler.__file__).parent / 'cli'
        if cli_path.exists():
            print(f"   CLI module found at: {cli_path}")
            return True
        else:
            print(f"   CLI module not found at: {cli_path}")
            return False
            
    except ImportError as e:
        print(f"  ArticleCrawler not found: {e}")
        return False


def main():
    print("=" * 70)
    print("ARTICLECRAWLER CLI - SETUP CHECKER")
    print("=" * 70)
    
    print("\nPython Version:")
    python_ok = check_python_version()
    
    missing = check_dependencies()
    
    ac_ok = check_articlecrawler()
    
    print("\n" + "=" * 70)
    if python_ok and not missing and ac_ok:
        print(" SETUP COMPLETE - Ready to use CLI!")
        print("=" * 70)
        print("\nNext steps:")
        print("  1. Run demo: python Demo/demo_cli.py")
        print("  2. Start wizard: crawler wizard")
        print("  3. Or: python -m ArticleCrawler.cli.main wizard")
        return 0
    else:
        print("  SETUP INCOMPLETE")
        print("=" * 70)
        
        if not python_ok:
            print("\n Python 3.8+ required")
        
        if missing:
            print(f"\n Missing {len(missing)} dependencies:")
            for dep in missing:
                pkg_map = {
                    'yaml': 'pyyaml',
                    'typer': 'typer[all]'
                }
                pkg_name = pkg_map.get(dep, dep)
                print(f"     - {pkg_name}")
            
            print("\n   Install with:")
            print("     pip install -e '.[cli]'")
            print("\n   Or manually:")
            packages = ' '.join(pkg_map.get(d, d) for d in missing)
            print(f"     pip install {packages}")
        
        if not ac_ok:
            print("\n ArticleCrawler CLI module missing")
            print("   Make sure all CLI files are in ArticleCrawler/cli/")
        
        print("\n" + "=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())