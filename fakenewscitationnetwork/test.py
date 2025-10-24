
import sys
import os
import subprocess
import shutil
from pathlib import Path


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
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message):
    """Print an error message"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_warning(message):
    """Print a warning message"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def print_info(message):
    """Print an info message"""
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")


def check_pytest_installed():
    """Check if pytest is installed"""
    try:
        import pytest
        print_success(f"pytest is installed (version {pytest.__version__})")
        return True
    except ImportError:
        print_error("pytest is not installed!")
        print_info("Install it with: pip install pytest pytest-cov")
        return False


def check_docker_available():
    """Check if Docker is installed"""
    docker_cmd = shutil.which("docker")
    
    if docker_cmd is None:
        return False
    
    try:
        subprocess.run(
            ["docker", "ps"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def check_grobid_running():
    """Check if GROBID service is running (using is_alive endpoint)"""
    try:
        import requests
        response = requests.get(
            "http://localhost:8070/api/isalive",
            timeout=2
        )
        return response.status_code == 200
    except:
        return False


def run_pytest(test_paths, description, verbose=False):
    """Run pytest on specified test paths"""
    print_info(f"Running {description}...")
    
    cmd = [sys.executable, "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    cmd.extend(test_paths)
    
    cmd.extend([
        "--tb=short",
        "--no-header",
        "-p", "no:warnings",
    ])
    
    try:
        result = subprocess.run(
            cmd,
            cwd=Path.cwd(),
            text=True,
            capture_output=False
        )
        
        if result.returncode == 0:
            print_success(f"{description} passed!")
            return True
        else:
            print_error(f"{description} failed!")
            return False
            
    except Exception as e:
        print_error(f"Error running {description}: {e}")
        return False


def main():
    """Main test function"""
    print_header("ArticleCrawler Post-Installation Tests")
    print_info("Running essential tests to verify installation...\n")
    
    if not Path("tests").exists():
        print_error("tests directory not found!")
        print_info("Please run this script from the project root directory.")
        print_info("Expected location: OpenAlexProject/fakenewscitationnetwork/")
        sys.exit(1)
    
    if not check_pytest_installed():
        sys.exit(1)
    
    docker_available = check_docker_available()
    grobid_running = check_grobid_running()
    
    if not docker_available:
        print_warning("Docker is not available - skipping Docker-dependent tests")
        print_info("Install Docker to enable PDF processing features")
    elif not grobid_running:
        print_warning("Docker is available, but GROBID is not running")
        print_info("To run Docker tests, start GROBID in a separate terminal:")
        print(f"{Colors.OKCYAN}    docker run --rm -p 8070:8070 lfoppiano/grobid:0.8.2{Colors.ENDC}")
        print_info("Then run this test script again")
        print_info("\nSkipping Docker-dependent tests for now...")
    else:
        print_success("Docker is available and GROBID is running!")
    
    print()
    
    results = {}
    

    print_header("Core Unit Tests (No External Dependencies)")
    
    core_tests = [
        ("tests/unit/config/test_api_config.py", "API Configuration"),
        ("tests/unit/config/test_sampling_config.py", "Sampling Configuration"),
        ("tests/unit/config/test_storage_config.py", "Storage Configuration"),
        
        ("tests/unit/api/test_api_factory.py", "API Factory"),
        ("tests/unit/api/test_base_api.py", "Base API"),
        
        ("tests/unit/data/test_data_frame_store.py", "Data Frame Store"),
        ("tests/unit/data/test_metadata_parser.py", "Metadata Parser"),
        
        ("tests/unit/graph/test_graph_processing.py", "Graph Processing"),
        
        ("tests/unit/text_processing/test_preprocessing.py", "Text Preprocessing"),
        ("tests/unit/text_processing/test_vectorization.py", "Text Vectorization"),
        
        ("tests/unit/library/test_library_inputs.py", "Library Inputs"),
        ("tests/unit/library/test_library_validator.py", "Library Validator"),
        
        ("tests/unit/cli/test_validators.py", "CLI Validators"),
        ("tests/unit/cli/test_config_loader.py", "Config Loader"),
    ]
    
    print_info(f"Running {len(core_tests)} essential unit tests...\n")
    
    core_passed = 0
    core_failed = 0
    
    for test_path, description in core_tests:
        if Path(test_path).exists():
            if run_pytest([test_path], description):
                core_passed += 1
            else:
                core_failed += 1
        else:
            print_warning(f"Test not found: {test_path}")
    
    results["Core Tests"] = {"passed": core_passed, "failed": core_failed}
    

    print_header("Integration Tests (Basic Workflows)")
    
    integration_tests = [
        ("tests/integration/test_api_to_data_flow.py", "API to Data Flow"),
        ("tests/integration/test_data_to_graph_flow.py", "Data to Graph Flow"),
        ("tests/integration/test_sampling_workflow.py", "Sampling Workflow"),
    ]
    
    print_info(f"Running {len(integration_tests)} integration tests...\n")
    
    integration_passed = 0
    integration_failed = 0
    
    for test_path, description in integration_tests:
        if Path(test_path).exists():
            if run_pytest([test_path], description):
                integration_passed += 1
            else:
                integration_failed += 1
        else:
            print_warning(f"Test not found: {test_path}")
    
    results["Integration Tests"] = {"passed": integration_passed, "failed": integration_failed}
    

    if grobid_running:
        print_header("Docker-Dependent Tests (PDF Processing with GROBID)")
        
        docker_tests = [
            ("tests/unit/pdf/test_docker_manager.py", "Docker Manager"),
            ("tests/unit/pdf/test_grobid_client.py", "GROBID Client"),
            ("tests/unit/pdf/test_metadata_extractor.py", "PDF Metadata Extractor"),
            ("tests/integration/test_pdf_workflow_integration.py", "PDF Workflow Integration"),
        ]
        
        print_info(f"Running {len(docker_tests)} Docker-dependent tests...\n")
        
        docker_passed = 0
        docker_failed = 0
        
        for test_path, description in docker_tests:
            if Path(test_path).exists():
                if run_pytest([test_path], description):
                    docker_passed += 1
                else:
                    docker_failed += 1
            else:
                print_warning(f"Test not found: {test_path}")
        
        results["Docker Tests"] = {"passed": docker_passed, "failed": docker_failed}

    print_header("Test Summary")
    
    total_passed = 0
    total_failed = 0
    
    for category, counts in results.items():
        passed = counts["passed"]
        failed = counts["failed"]
        total = passed + failed
        
        total_passed += passed
        total_failed += failed
        
        if failed == 0:
            status = f"{Colors.OKGREEN}✓ ALL PASSED{Colors.ENDC}"
        else:
            status = f"{Colors.FAIL}✗ {failed} FAILED{Colors.ENDC}"
        
        print(f"{Colors.BOLD}{category}:{Colors.ENDC} {passed}/{total} passed {status}")
    
    print()
    print(f"{Colors.BOLD}Total:{Colors.ENDC} {total_passed} passed, {total_failed} failed")
    

    print()
    
    if total_failed == 0:
        print_header("✓ Installation Verified Successfully!")
        print_success("All essential tests passed!")
        print_info("Your ArticleCrawler installation is ready to use.\n")
        
        print(f"{Colors.BOLD}Next Steps:{Colors.ENDC}")
        print(f"  2. Run: python -m ArticleCrawler.cli.main wizard")
        print(f"  3. Follow the interactive setup to start crawling!\n")
        
        if not grobid_running:
            if docker_available:
                print_warning("Note: GROBID is not running.")
                print_info("PDF processing features require GROBID to be started.")
                print_info("To start GROBID, run in a separate terminal:")
                print(f"  {Colors.OKCYAN}docker run --rm -p 8070:8070 lfoppiano/grobid:0.8.2{Colors.ENDC}\n")
            else:
                print_warning("Note: Docker is not available.")
                print_info("PDF processing features will not work without Docker + GROBID.")
                print_info("Install Docker if you need PDF processing capabilities.\n")
        
        return 0
    else:
        print_header("⚠ Installation Verification Issues")
        print_warning(f"{total_failed} test(s) failed!")
        print_info("\nPossible issues:")
        print_info("  - Missing dependencies")
        print_info("  - Environment variables not configured (.env file)")
        print_info("  - Python version incompatibility")
        print()
        print_info("Try running the full test suite for more details:")
        print(f"  {Colors.OKCYAN}pytest tests/ -v{Colors.ENDC}")
        print()
        
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Tests cancelled by user.{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print_error(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)