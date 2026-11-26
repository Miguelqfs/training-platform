#!/usr/bin/env bash
set -euo pipefail
# Fase 1 (padrão): abre o PR develop → main.
# Fase 2, depois do merge desse PR e do CI verde: bash scripts/rafael-git/10-release-v0.4.0.sh tag
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
git fetch origin develop main
mode="${1:-pr}"
if [[ "$mode" == "tag" ]]; then
  git checkout main
  git pull origin main
  git tag -a v0.4.0 -m "$(cat <<'EOF'
Sprint 5: fachada em Command, Memento e desfazer a última atualização do treino.

EOF
)"
  git push origin v0.4.0
  echo "Tag v0.4.0 publicada em $(git rev-parse --short v0.4.0)."
  exit 0
fi
gh pr create --base main --head develop --title "release: Sprint 5 v0.4.0" --body "$(cat <<'EOF'
## Summary

Integra a Sprint 5 em main: fachada baseada em Command, persistência do Memento e desfazer da última atualização do treino. A tag v0.4.0 entra depois do merge, no commit de main.

## Test plan

- [x] CI verde em develop no fechamento documental
- [x] Checklist docs/sprint5/fechamento-checklist.md, exceto o merge desta release
- [ ] Checks deste PR verdes antes do merge
- [ ] Depois do merge: bash scripts/rafael-git/10-release-v0.4.0.sh tag

EOF
)"
