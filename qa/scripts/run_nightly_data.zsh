#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

print_phase() {
  printf '\n==> %s\n' "$1"
}

print_phase "Data integrity"
python3 qa/scripts/check_data_integrity.py --reseed

print_phase "Data freshness"
python3 qa/scripts/check_data_freshness.py --reseed

print_phase "Official link health"
python3 qa/scripts/check_link_health.py --reseed --sample-size 25
