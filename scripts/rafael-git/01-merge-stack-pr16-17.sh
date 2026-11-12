#!/usr/bin/env bash
set -euo pipefail
# PRs empilhados: merge-async no PR do topo (#17); inclui downstack (#16).
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
SHA="$(gh api repos/Miguelqfs/training-platform/pulls/17 --jq .head.sha)"
gh api -X PUT "repos/Miguelqfs/training-platform/pulls/17/merge-async" \
  -f merge_method=merge \
  -f merge_action=direct_merge \
  -f "sha=${SHA}"
for _ in $(seq 1 15); do
  S16="$(gh pr view 16 --json state --jq .state)"
  S17="$(gh pr view 17 --json state --jq .state)"
  if [[ "$S16" == "MERGED" && "$S17" == "MERGED" ]]; then
  echo "PRs #16 e #17 merged."
    exit 0
  fi
  sleep 2
done
echo "Timeout aguardando merge." >&2
exit 1
