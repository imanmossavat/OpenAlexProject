import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
CLI_DIR = ROOT_DIR / "fakenewscitationnetwork"
BACKEND_DIR = ROOT_DIR / "article-crawler-backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
VENV_PATH = ROOT_DIR / ".venv"
DEFAULT_CORS = ["http://localhost:5173", "http://localhost:3000"]


class Colors:
    HEADER = "\033[96m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_header(message: str) -> None:
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")


def print_success(message: str) -> None:
    print(f"{Colors.OKGREEN}[OK] {message}{Colors.ENDC}")


def print_error(message: str) -> None:
    print(f"{Colors.FAIL}[ERROR] {message}{Colors.ENDC}")


def print_warning(message: str) -> None:
    print(f"{Colors.WARNING}[WARNING] {message}{Colors.ENDC}")


def print_info(message: str) -> None:
    print(f"{Colors.OKCYAN}[INFO] {message}{Colors.ENDC}")


def prompt_yes_no(question: str, default: bool = True) -> bool:
    options = "Y/n" if default else "y/N"
    while True:
        answer = input(f"{question} ({options}): ").strip().lower()
        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print_warning("Please enter 'y' or 'n'.")


def prompt_with_default(question: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    answer = input(f"{question}{suffix}: ").strip()
    return answer or default


def prompt_required(question: str) -> str:
    while True:
        value = input(f"{question}: ").strip()
        if value:
            return value
        print_warning("This field is required.")


def ensure_project_structure() -> None:
    missing = [path for path in (CLI_DIR, BACKEND_DIR, FRONTEND_DIR) if not path.exists()]
    if missing:
        for path in missing:
            print_error(f"Missing required directory: {path}")
        print_error("Run this script from the OpenAlexProject root directory.")
        sys.exit(1)


def check_python_version() -> None:
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    if not (
        version.major == 3
        and 10 <= version.minor <= 12
    ):
        print_error(
            f"Python 3.10–3.12 is required. Detected {version_str}."
        )
        sys.exit(1)

    print_success(f"Python {version_str} detected.")



def parse_bool_env(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def parse_cors_list(raw: str | None) -> list[str]:
    if not raw:
        return DEFAULT_CORS.copy()
    stripped = raw.strip()
    if stripped.startswith("["):
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, list):
                return [str(item) for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            print_warning("Failed to parse BACKEND_CORS_ORIGINS as JSON. Falling back to comma parsing.")
    parts = [segment.strip() for segment in stripped.split(",") if segment.strip()]
    return parts or DEFAULT_CORS.copy()


def gather_env_inputs(non_interactive: bool = False) -> dict:
    print_header("Configuring Environment Values")
    if not non_interactive:
        openalex_email = prompt_required(f"{Colors.BOLD}OpenAlex email (required){Colors.ENDC}")
        print_info("Zotero configuration is optional. Leave fields empty to skip.")
        zotero_library_id = input("Zotero Library ID: ").strip()
        zotero_api_key = input("Zotero API Key: ").strip()
        zotero_library_type = prompt_with_default("Zotero Library Type (user/group)", "user")
        library_root = (CLI_DIR / "libraries").resolve().as_posix()
        backend_project_name = "ArticleCrawler API"
        backend_version = "1.0.0"
        backend_debug = True
        backend_log_level = "INFO"
        cors_list = DEFAULT_CORS.copy()
        frontend_api_url = "http://localhost:8000"
        grobid_url = "http://localhost:8070"
    else:
        def require_env(name: str) -> str:
            value = os.getenv(name, "").strip()
            if not value:
                print_error(f"{name} must be set when running non-interactively.")
                sys.exit(1)
            return value

        def optional_env(name: str, default: str = "") -> str:
            value = os.getenv(name)
            return value.strip() if isinstance(value, str) and value.strip() else default

        openalex_email = require_env("OPENALEX_EMAIL")
        zotero_library_id = optional_env("ZOTERO_LIBRARY_ID")
        zotero_api_key = optional_env("ZOTERO_API_KEY")
        zotero_library_type = optional_env("ZOTERO_LIBRARY_TYPE", "user")
        library_root = optional_env(
            "ARTICLECRAWLER_LIBRARY_ROOT",
            (CLI_DIR / "libraries").resolve().as_posix(),
        )
        backend_project_name = optional_env("PROJECT_NAME", "ArticleCrawler API")
        backend_version = optional_env("BACKEND_VERSION", "1.0.0")
        backend_debug = parse_bool_env(os.getenv("BACKEND_DEBUG"), True)
        backend_log_level = optional_env("LOG_LEVEL", "INFO")
        cors_list = parse_cors_list(os.getenv("BACKEND_CORS_ORIGINS"))
        frontend_api_url = optional_env("FRONTEND_API_URL") or optional_env("VITE_API_URL", "http://localhost:8000")
        grobid_url = optional_env("GROBID_URL", "http://localhost:8070")

    return {
        "openalex_email": openalex_email,
        "zotero_library_id": zotero_library_id,
        "zotero_api_key": zotero_api_key,
        "zotero_library_type": zotero_library_type or "user",
        "library_root": library_root,
        "backend_project_name": backend_project_name,
        "backend_version": backend_version,
        "backend_debug": backend_debug,
        "backend_log_level": backend_log_level,
        "backend_cors_origins": cors_list or DEFAULT_CORS.copy(),
        "frontend_api_url": frontend_api_url,
        "grobid_url": grobid_url,
    }


def write_file_with_prompt(path: Path, content: str, force: bool = False) -> None:
    if path.exists() and not force:
        overwrite = prompt_yes_no(f"{path} already exists. Overwrite?", False)
        if not overwrite:
            print_warning(f"Skipping {path}.")
            return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        file.write(content)
    print_success(f"Wrote {path}.")


def write_cli_env(values: dict, force: bool = False) -> None:
    lines = [
        "# OpenAlex Configuration",
        f"OPENALEX_EMAIL={values['openalex_email']}",
        "",
        "# Zotero Configuration (Optional)",
        (
            f"ZOTERO_LIBRARY_ID={values['zotero_library_id']}"
            if values["zotero_library_id"]
            else "# ZOTERO_LIBRARY_ID=your_library_id"
        ),
        f"ZOTERO_LIBRARY_TYPE={values['zotero_library_type']}",
        (
            f"ZOTERO_API_KEY={values['zotero_api_key']}"
            if values["zotero_api_key"]
            else "# ZOTERO_API_KEY=your_api_key"
        ),
        "",
        "# Storage",
        f'ARTICLECRAWLER_LIBRARY_ROOT="{values["library_root"]}"',
        "",
        "# Services",
        f"GROBID_URL={values['grobid_url']}",
        "",
    ]
    content = "\n".join(lines)
    write_file_with_prompt(CLI_DIR / ".env", content, force=force)


def write_backend_env(values: dict, force: bool = False) -> None:
    cors = "[" + ",".join(f'"{origin}"' for origin in values["backend_cors_origins"]) + "]"
    articlecrawler_path = CLI_DIR.resolve().as_posix()
    lines = [
        f'ARTICLECRAWLER_PATH="{articlecrawler_path}"',
        f'PROJECT_NAME="{values["backend_project_name"]}"',
        f'VERSION="{values["backend_version"]}"',
        f"DEBUG={str(values['backend_debug']).lower()}",
        f"LOG_LEVEL={values['backend_log_level']}",
        f"BACKEND_CORS_ORIGINS={cors}",
        f"OPENALEX_EMAIL={values['openalex_email']}",
        f"ZOTERO_LIBRARY_ID={values['zotero_library_id']}",
        f"ZOTERO_LIBRARY_TYPE={values['zotero_library_type']}",
        f"ZOTERO_API_KEY={values['zotero_api_key']}",
        f'ARTICLECRAWLER_LIBRARY_ROOT="{values["library_root"]}"',
        f"GROBID_URL={values['grobid_url']}",
        "",
    ]
    content = "\n".join(lines)
    write_file_with_prompt(BACKEND_DIR / ".env", content, force=force)


def write_frontend_env(values: dict, force: bool = False) -> None:
    content = f"VITE_API_URL={values['frontend_api_url']}\n"
    write_file_with_prompt(FRONTEND_DIR / ".env", content, force=force)


def upgrade_pip(pip_exe: Path) -> bool:
    print_info("Upgrading pip to the latest version...")
    if pip_run(pip_exe, ["install", "--upgrade", "pip"]):
        print_success("pip upgraded successfully.")
        return True
    print_warning("pip upgrade failed.")
    return False


def install_cli_editable(pip_exe: Path) -> bool:
    print_info("Installing ArticleCrawler package (editable)...")
    if pip_run(pip_exe, ["install", "-e", str(CLI_DIR.resolve())]):
        print_success("ArticleCrawler installed (editable).")
        return True
    print_error("Failed to install ArticleCrawler (editable).")
    return False


def install_cli_requirements(pip_exe: Path) -> bool:
    requirements = CLI_DIR / "requirements.txt"
    if not requirements.exists():
        print_warning(f"CLI requirements file not found at {requirements}, skipping.")
        return True
    print_info("Installing CLI pinned requirements...")
    if pip_run(pip_exe, ["install", "-r", str(requirements)]):
        print_success("CLI requirements installed.")
        return True
    print_error("Failed to install CLI requirements.")
    return False


def download_nltk_data(python_exe: Path) -> bool:
    packages = ["stopwords", "punkt", "wordnet", "omw-1.4"]
    print_info("Downloading required NLTK datasets...")
    success = True
    for pkg in packages:
        print_info(f"  - {pkg}")
        cmd = [str(python_exe), "-c", f"import nltk; nltk.download('{pkg}', quiet=True)"]
        if not run_subprocess(cmd):
            success = False
            print_warning(f"Failed to download {pkg}.")
    if success:
        print_success("NLTK data downloaded.")
    return success


def check_docker() -> None:
    docker_cmd = shutil.which("docker")
    if docker_cmd is None:
        print_warning("Docker is not installed or not on PATH. PDF parsing via GROBID will not work.")
        return
    print_success("Docker detected.")
    try:
        subprocess.run([docker_cmd, "ps"], check=True, capture_output=True)
        print_success("Docker daemon is running.")
    except subprocess.CalledProcessError:
        print_warning("Docker installed but not running. Start Docker Desktop before PDF parsing.")


def print_grobid_instructions() -> None:
    print_header("GROBID Setup (Optional, for PDF parsing)")
    print("1. Pull the Docker image:")
    print(f"   {Colors.OKCYAN}docker pull lfoppiano/grobid:0.8.2{Colors.ENDC}")
    print("2. Run it in a separate terminal whenever PDFs are processed:")
    print(f"   {Colors.OKCYAN}docker run --rm -p 8070:8070 lfoppiano/grobid:0.8.2{Colors.ENDC}")
    print("Keep that terminal open while jobs run.")


def run_subprocess(command: list[str], cwd: Path | None = None) -> bool:
    try:
        subprocess.run(command, cwd=cwd, check=True)
        return True
    except subprocess.CalledProcessError as exc:
        cmd_str = " ".join(command)
        print_error(f"Command failed ({cmd_str}): {exc}")
        return False


def pip_run(pip_executable: Path, args: list[str], cwd: Path | None = None) -> bool:
    return run_subprocess([str(pip_executable), *args], cwd=cwd)


def create_virtualenv(venv_path: Path) -> bool:
    if venv_path.exists():
        recreate = prompt_yes_no(f"{venv_path} already exists. Recreate it?", False)
        if recreate:
            shutil.rmtree(venv_path)
        else:
            print_info("Keeping existing virtual environment.")
            return True
    print_info(f"Creating virtual environment at {venv_path}...")
    return run_subprocess([sys.executable, "-m", "venv", str(venv_path)])


def get_venv_executable(venv_path: Path, name: str) -> Path:
    scripts_dir = "Scripts" if platform.system() == "Windows" else "bin"
    return venv_path / scripts_dir / name


def get_activation_command(venv_path: Path) -> str:
    if platform.system() == "Windows":
        return f"{venv_path}\\Scripts\\activate"
    return f"source {venv_path}/bin/activate"


def install_backend_dependencies(pip_exe: Path) -> bool:
    requirements = BACKEND_DIR / "requirements.txt"
    if not requirements.exists():
        print_error(f"Backend requirements file not found: {requirements}")
        return False

    filtered_lines = []
    with open(requirements, "r", encoding="utf-8") as source:
        for line in source:
            stripped = line.strip()
            if stripped.startswith("-e"):
                continue
            filtered_lines.append(line)

    temp_requirements = BACKEND_DIR / "requirements.generated.txt"
    with open(temp_requirements, "w", encoding="utf-8") as temp:
        temp.writelines(filtered_lines)

    print_info("Installing backend dependencies into the project virtual environment...")
    success = pip_run(pip_exe, ["install", "-r", str(temp_requirements)])
    temp_requirements.unlink(missing_ok=True)
    return success


def setup_python_environment() -> None:
    print_header("Python Virtual Environment Setup")
    if not create_virtualenv(VENV_PATH):
        print_warning("Virtual environment setup skipped.")
        return

    pip_name = "pip.exe" if platform.system() == "Windows" else "pip"
    python_name = "python.exe" if platform.system() == "Windows" else "python"
    pip_exe = get_venv_executable(VENV_PATH, pip_name)
    python_exe = get_venv_executable(VENV_PATH, python_name)

    if not pip_exe.exists() or not python_exe.exists():
        print_error("Failed to locate pip/python inside the virtual environment.")
        return

    upgrade_pip(pip_exe)
    if not install_cli_requirements(pip_exe):
        return
    if not install_cli_editable(pip_exe):
        return
    if not download_nltk_data(python_exe):
        print_warning("Continuing despite NLTK download issues.")
    if not install_backend_dependencies(pip_exe):
        return

    check_docker()
    print_success(f"Python dependencies installed inside {VENV_PATH}.")
    activation_cmd = get_activation_command(VENV_PATH)
    print_info(f"Activate this environment with: {activation_cmd}")
    print_grobid_instructions()


def setup_frontend_dependencies() -> None:
    print_header("Frontend Setup")
    if not prompt_yes_no("Run npm install for the frontend now?", True):
        print_warning("Skipping frontend dependency install.")
        return

    npm_cmd = shutil.which("npm")
    if not npm_cmd:
        print_error("npm is not installed or not found on PATH.")
        return

    if run_subprocess([npm_cmd, "install"], cwd=FRONTEND_DIR):
        print_success("Frontend dependencies installed.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ArticleCrawler installer")
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Read config values from environment variables instead of prompting.",
    )
    parser.add_argument(
        "--env-only",
        action="store_true",
        help="Only generate .env files (skip dependency installation).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing .env files without prompting (implied in non-interactive mode).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print_header("ArticleCrawler Full-Stack Installer")
    ensure_project_structure()
    check_python_version()

    values = gather_env_inputs(non_interactive=args.non_interactive)
    force_write = args.force or args.non_interactive
    write_cli_env(values, force=force_write)
    write_backend_env(values, force=force_write)
    write_frontend_env(values, force=force_write)

    if not args.env_only:
        setup_python_environment()
        setup_frontend_dependencies()

    print_header("All Done")
    print_success("Environment files are configured.")
    print_info("Next steps:")
    print("  - Activate the virtual environment:")
    if platform.system() == "Windows":
        print("      .venv\\Scripts\\activate")
    else:
        print("      source .venv/bin/activate")
    print("  - Start Docker + GROBID if you need PDF parsing.")
    print("  - Use the activated environment to run CLI commands or the API (uvicorn).")
    print("  - Run `npm run dev` from the frontend directory.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_warning("Setup cancelled by user.")
        sys.exit(1)
    except Exception as exc:
        print_error(f"Unexpected error: {exc}")
        sys.exit(1)
