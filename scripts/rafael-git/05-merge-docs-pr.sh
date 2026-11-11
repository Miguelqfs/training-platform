#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
PR_NUM="$(gh pr list --head docs/sprint4-projeto-rafael --json number --jq '.[0].number')"
if [[ -z "$PR_NUM" || "$PR_NUM" == "null" ]]; then
  echo "Nenhum PR aberto para docs/sprint4-projeto-rafael" >&2
  exit 1
fi
gh pr merge "$PR_NUM" --merge
