#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

print_phase() {
  printf '\n==> %s\n' "$1"
}

print_phase "Lint"
pnpm lint

print_phase "Typecheck"
pnpm typecheck

print_phase "Unit and API tests"
pnpm test

print_phase "Data integrity"
python3 qa/scripts/check_data_integrity.py --reseed

print_phase "Data freshness"
python3 qa/scripts/check_data_freshness.py --reseed

print_phase "Official link health"
python3 qa/scripts/check_link_health.py --reseed --sample-size 25

print_phase "Critical E2E"
exec python3 qa/scripts/run_critical_e2e.py
