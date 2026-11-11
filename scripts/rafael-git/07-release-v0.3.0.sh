#!/usr/bin/env bash
set -euo pipefail
# Rodar após checklist docs/sprint4/fechamento-checklist.md
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
git fetch origin develop main
git checkout main
git pull origin main
git merge origin/develop --no-edit
git tag -a v0.3.0 -m "$(cat <<'EOF'
Sprint 4: eventos de acesso, relatório HTML/PDF, padrões da disciplina.
EOF
)"
git push origin main
git push origin v0.3.0
echo "Crie o PR develop→main no GitHub se a equipe preferir revisão antes do push direto."
gh pr create --base main --head develop --title "release: Sprint 4 v0.3.0" --body "$(cat <<'EOF'
## Summary

Integração da change relatorio-de-acessos em main com tag v0.3.0.

## Test plan

- [ ] CI verde em develop
- [ ] Checklist docs/sprint4/fechamento-checklist.md
EOF
)" || true
