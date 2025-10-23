import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

if platform.system() == "Windows":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[96m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(message):
    """Print a formatted header message"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")


def print_success(message):
    """Print a success message"""
    print(f"{Colors.OKGREEN}[OK] {message}{Colors.ENDC}")


def print_error(message):
    """Print an error message"""
    print(f"{Colors.FAIL}[ERROR] {message}{Colors.ENDC}")


def print_warning(message):
    """Print a warning message"""
    print(f"{Colors.WARNING}[WARNING] {message}{Colors.ENDC}")


def print_info(message):
    """Print an info message"""
    print(f"{Colors.OKCYAN}[INFO] {message}{Colors.ENDC}")


def check_python_version():
    """Check if Python version is 3.10 or higher"""
    print_header("Checking Python Version")
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    print_info(f"Current Python version: {version_str}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print_error(f"Python 3.10 or higher is required. You have {version_str}")
        print_info("Please install Python 3.10 or higher from https://www.python.org/downloads/")
        print_warning("Python 3.8 and 3.9 have compatibility issues with certain dependencies.")
        return False
    
    print_success(f"Python version {version_str} is compatible!")
    return True


def get_venv_path():
    """Get the path for virtual environment based on OS"""
    return Path("venv")


def get_activation_command():
    """Get the correct activation command based on OS"""
    system = platform.system()
    venv_path = get_venv_path()
    
    if system == "Windows":
        return f"{venv_path}\\Scripts\\activate"
    else:
        return f"source {venv_path}/bin/activate"


def create_virtual_environment():
    """Create a virtual environment"""
    print_header("Creating Virtual Environment")
    
    venv_path = get_venv_path()
    
    if venv_path.exists():
        print_warning(f"Virtual environment '{venv_path}' already exists.")
        response = input("Do you want to delete and recreate it? (y/n): ").lower()
        if response == 'y':
            print_info(f"Removing existing virtual environment...")
            shutil.rmtree(venv_path)
        else:
            print_info("Using existing virtual environment.")
            return True
    
    try:
        print_info(f"Creating virtual environment at '{venv_path}'...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
        print_success(f"Virtual environment created successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to create virtual environment: {e}")
        return False


def get_pip_executable():
    """Get the path to pip in the virtual environment"""
    venv_path = get_venv_path()
    system = platform.system()
    
    if system == "Windows":
        return venv_path / "Scripts" / "pip.exe"
    else:
        return venv_path / "bin" / "pip"


def get_python_executable():
    """Get the path to python in the virtual environment"""
    venv_path = get_venv_path()
    system = platform.system()
    
    if system == "Windows":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"


def upgrade_pip():
    """Upgrade pip in the virtual environment"""
    print_header("Upgrading pip")
    
    pip_exe = get_pip_executable()
    
    try:
        print_info("Upgrading pip to the latest version...")
        subprocess.run([str(pip_exe), "install", "--upgrade", "pip"], check=True, capture_output=True)
        print_success("pip upgraded successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to upgrade pip: {e}")
        return False


def install_dependencies():
    """Install project dependencies"""
    print_header("Installing Dependencies")
    
    pip_exe = get_pip_executable()
    
    if not Path("pyproject.toml").exists():
        print_error("pyproject.toml not found in current directory!")
        print_info("Please run this script from the project root directory (fakenewscitationnetwork)")
        return False
    
    try:
        print_info("Installing package with dependencies (this may take several minutes)...")
        print_info("This will install all required packages...")
        
        result = subprocess.run(
            [str(pip_exe), "install", "-e", ".[cli,dev]"],
            check=True,
            text=True,
            capture_output=False
        )
        
        print_success("Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies")
        print_warning("\nYou may need to install dependencies manually:")
        print_warning(f"  1. Activate the environment: {get_activation_command()}")
        print_warning(f"  2. Install dependencies: pip install -e \".[cli,dev]\"")
        return False


def download_nltk_data():
    """Download required NLTK data"""
    print_header("Downloading NLTK Data")
    
    python_exe = get_python_executable()
    
    nltk_packages = ['stopwords', 'punkt', 'wordnet', 'omw-1.4']
    
    try:
        print_info("Downloading NLTK datasets...")
        for package in nltk_packages:
            print_info(f"  - Downloading '{package}'...")
            subprocess.run([
                str(python_exe), "-c",
                f"import nltk; nltk.download('{package}', quiet=True)"
            ], check=True, capture_output=True)
        
        print_success("NLTK data downloaded successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to download NLTK data: {e}")
        return False


def check_docker():
    """Check if Docker is installed and running"""
    print_header("Checking Docker Installation")
    
    docker_cmd = shutil.which("docker")
    
    if docker_cmd is None:
        print_error("Docker is not installed!")
        print_warning("Docker is required for PDF processing with GROBID.")
        print_info("\nTo install Docker:")
        print_info("  Windows: https://www.docker.com/products/docker-desktop")
        print_info("  macOS:   https://www.docker.com/products/docker-desktop")
        print_info("  Linux:   https://docs.docker.com/engine/install/")
        return False
    
    print_success("Docker is installed!")
    
    try:
        result = subprocess.run(
            ["docker", "ps"],
            check=True,
            capture_output=True,
            text=True
        )
        print_success("Docker is running!")
        return True
    except subprocess.CalledProcessError:
        print_warning("Docker is installed but not running.")
        print_info("Please start Docker Desktop before processing PDFs.")
        return True


def setup_env_file():
    """Guide user through .env file setup"""
    print_header("Configuring Environment Variables")
    
    env_file = Path(".env")
    env_template = Path("_env")
    
    if env_file.exists():
        print_warning(".env file already exists.")
        response = input("Do you want to reconfigure it? (y/n): ").lower()
        if response != 'y':
            print_info("Keeping existing .env file.")
            return True
    
    if not env_template.exists():
        print_warning("_env template file not found. Creating minimal .env file...")
    
    print_info("\nLet's configure your environment variables.")
    print_info("Press Enter to skip optional fields.\n")
    
    openalex_email = ""
    while not openalex_email:
        openalex_email = input(f"{Colors.BOLD}OpenAlex Email (REQUIRED):{Colors.ENDC} ").strip()
        if not openalex_email:
            print_warning("OpenAlex email is required for the application to work!")
    
    print_info("\nZotero configuration (optional - only needed for Zotero integration):")
    zotero_library_id = input(f"{Colors.BOLD}Zotero Library ID (optional):{Colors.ENDC} ").strip()
    zotero_api_key = input(f"{Colors.BOLD}Zotero API Key (optional):{Colors.ENDC} ").strip()
    zotero_library_type = "user"
    
    if zotero_library_id or zotero_api_key:
        lib_type = input(f"{Colors.BOLD}Zotero Library Type (user/group) [user]:{Colors.ENDC} ").strip()
        if lib_type:
            zotero_library_type = lib_type
    
    try:
        with open(env_file, 'w') as f:
            f.write("# OpenAlex Configuration (Required)\n")
            f.write(f"OPENALEX_EMAIL={openalex_email}\n\n")
            
            f.write("# Zotero Configuration (Optional - only needed for Zotero integration)\n")
            if zotero_library_id:
                f.write(f"ZOTERO_LIBRARY_ID={zotero_library_id}\n")
            else:
                f.write("# ZOTERO_LIBRARY_ID=your_library_id\n")
            
            if zotero_api_key:
                f.write(f"ZOTERO_API_KEY={zotero_api_key}\n")
            else:
                f.write("# ZOTERO_API_KEY=your_api_key\n")
            
            f.write(f"ZOTERO_LIBRARY_TYPE={zotero_library_type}\n")
        
        print_success(".env file created successfully!")
        return True
    except Exception as e:
        print_error(f"Failed to create .env file: {e}")
        return False


def print_grobid_instructions():
    """Print instructions for starting GROBID"""
    print_header("GROBID Setup Instructions")
    
    print_info("GROBID is required for PDF processing.")
    print_info("You need to run GROBID in a SEPARATE terminal window.\n")
    
    print(f"{Colors.BOLD}Step 1: Pull the GROBID Docker image{Colors.ENDC}")
    print(f"{Colors.OKCYAN}    docker pull lfoppiano/grobid:0.8.2{Colors.ENDC}\n")
    
    print(f"{Colors.BOLD}Step 2: Start GROBID (in a separate terminal){Colors.ENDC}")
    print(f"{Colors.OKCYAN}    docker run --rm -p 8070:8070 lfoppiano/grobid:0.8.2{Colors.ENDC}\n")
    
    print(f"{Colors.WARNING}Important:{Colors.ENDC}")
    print(f"  - Keep the GROBID terminal window open while processing PDFs")
    print(f"  - Wait 30-60 seconds for GROBID to fully start before processing PDFs\n")


def print_next_steps():
    """Print next steps for the user"""
    print_header("Setup Complete!")
    
    activation_cmd = get_activation_command()
    
    print(f"{Colors.OKGREEN}{Colors.BOLD}Installation successful!{Colors.ENDC}\n")
    
    print(f"{Colors.BOLD}Next Steps:{Colors.ENDC}\n")
    
    print(f"{Colors.BOLD}1. Activate the virtual environment:{Colors.ENDC}")
    if platform.system() == "Windows":
        print(f"{Colors.OKCYAN}    venv\\Scripts\\activate{Colors.ENDC}\n")
    else:
        print(f"{Colors.OKCYAN}    source venv/bin/activate{Colors.ENDC}\n")
    
    print(f"{Colors.BOLD}2. (Optional) Start GROBID for PDF processing:{Colors.ENDC}")
    print(f"{Colors.OKCYAN}    docker run --rm -p 8070:8070 lfoppiano/grobid:0.8.2{Colors.ENDC}\n")
    
    print(f"{Colors.BOLD}3. Start using ArticleCrawler:{Colors.ENDC}")
    print(f"{Colors.OKCYAN}    python -m ArticleCrawler.cli.main wizard{Colors.ENDC}\n")
    
    print(f"{Colors.BOLD}Available Commands:{Colors.ENDC}")
    print(f"  - {Colors.OKCYAN}python -m ArticleCrawler.cli.main wizard{Colors.ENDC}           - Interactive setup wizard")
    print(f"  - {Colors.OKCYAN}python -m ArticleCrawler.cli.main library-create{Colors.ENDC}   - Create literature library")
    print(f"  - {Colors.OKCYAN}python -m ArticleCrawler.cli.main topic-modeling{Colors.ENDC}   - Discover topics")
    print(f"  - {Colors.OKCYAN}python -m ArticleCrawler.cli.main author-evolution{Colors.ENDC} - Track author evolution")
    print(f"  - {Colors.OKCYAN}python -m ArticleCrawler.cli.main edit{Colors.ENDC}             - Edit configurations\n")


def main():
    """Main setup function"""
    print_header("ArticleCrawler Setup Script")
    print_info("This script will set up your ArticleCrawler environment.\n")
    
    if not Path("pyproject.toml").exists():
        print_error("This script must be run from the project root directory!")
        print_info("Expected location: OpenAlexProject/fakenewscitationnetwork/")
        print_info("Please navigate to the correct directory and run the script again.")
        sys.exit(1)
    
    if not check_python_version():
        sys.exit(1)
    
    if not create_virtual_environment():
        sys.exit(1)
    
    if not upgrade_pip():
        print_warning("Continuing despite pip upgrade failure...")
    
    if not install_dependencies():
        sys.exit(1)
    
    if not download_nltk_data():
        print_warning("Continuing despite NLTK download issues...")
    
    if not setup_env_file():
        print_warning("Continuing despite .env setup issues...")
    
    check_docker()
    
    print_grobid_instructions()
    
    print_next_steps()
    
    print(f"\n{Colors.OKGREEN}{Colors.BOLD}Setup completed successfully!{Colors.ENDC}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Setup cancelled by user.{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print_error(f"An unexpected error occurred: {e}")
        sys.exit(1)