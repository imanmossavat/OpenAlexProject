#!/usr/bin/env bash
set -euo pipefail

BOOTSTRAP_TARGETS=(
  "/app/fakenewscitationnetwork/.env"
  "/app/article-crawler-backend/.env"
  "/app/frontend/.env"
)

needs_bootstrap=false
for target in "${BOOTSTRAP_TARGETS[@]}"; do
  if [[ ! -f "${target}" ]]; then
    needs_bootstrap=true
    break
  fi
done

if [[ "${SKIP_BOOTSTRAP:-0}" != "1" ]]; then
  if [[ "${needs_bootstrap}" == "true" ]]; then
    echo "Generating environment files via install.py..."
    python install.py --non-interactive --env-only --force
  else
    echo "Environment files already present. Skipping bootstrap."
  fi
else
  echo "Skipping bootstrap because SKIP_BOOTSTRAP=1."
fi

exec "$@"
