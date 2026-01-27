from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
COMPONENTS = {
    "crawler": ROOT / "fakenewscitationnetwork",
    "backend": ROOT / "article-crawler-backend",
}
BACKEND_ENV = COMPONENTS["backend"] / ".env"


def load_env_file(env_path: Path) -> dict:
    env = os.environ.copy()
    if not env_path.exists():
        raise FileNotFoundError(f"{env_path} missing. Run install.py or create the .env first.")

    for raw_line in env_path.read_text().splitlines():
        cleaned = raw_line.strip()
        if not cleaned or cleaned.startswith("#"):
            continue
        key, _, value = cleaned.partition("=")
        env[key.strip()] = value.strip().strip("\"'")
    return env


def run_pytest(component: str) -> int:
    path = COMPONENTS[component]
    base_args: list[str] = []
    if component == "backend":
        base_args.extend(["-p", "no:warnings"])
    cmd = [sys.executable, "-m", "pytest", *base_args]
    print(f"\n=== Running tests for {component} ({path}) ===")
    env = None
    if component == "backend":
        try:
            env = load_env_file(BACKEND_ENV)
        except FileNotFoundError as exc:
            print(f"Error loading backend .env: {exc}")
            return 1
    result = subprocess.run(cmd, cwd=path, env=env)
    return result.returncode


def main() -> int:
    exit_code = 0
    for component in COMPONENTS:
        result = run_pytest(component)
        if result != 0 and exit_code == 0:
            exit_code = result
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
