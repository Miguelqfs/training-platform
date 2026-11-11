#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
git fetch origin develop
git checkout -B docs/sprint4-handoff origin/develop
git add \
  README.md \
  docs/03-elicitacao.md \
  docs/08-projeto.md \
  docs/04-casos-de-uso/ \
  docs/adr/0007-adapter-log-eventos.md \
  docs/adr/0008-relatorio-template-method.md \
  docs/diagramas/casos-de-uso-usuarios.puml \
  docs/diagramas/diagrama-casos-de-uso.png \
  docs/sprint4/ \
  scripts/rafael-git/06-archive-openspec-change.sh \
  scripts/rafael-git/07-release-v0.3.0.sh \
  scripts/rafael-git/08-handoff-commit-push-pr.sh
git status
if git diff --cached --quiet; then
  echo "Nada para commitar." >&2
  exit 1
fi
git commit -m "$(cat <<'EOF'
docs(sprint4): handoff Luigi/Miguel, UC09 e fechamento

Guias de implementação, ADRs esqueleto, casos de uso com eventos e relatório,
README e scripts de archive/release para minimizar trabalho pós-integração.
EOF
)"
git push -u origin docs/sprint4-handoff
gh pr create --base develop --head docs/sprint4-handoff \
  --title "docs(sprint4): handoff, UC09 e checklist de release" \
  --body "$(cat <<'EOF'
## Resumo

- Índice e guias em `docs/sprint4/` para Luigi (registro + Adapter) e Miguel (Template Method + API).
- UC03–UC07, UC09, diagrama de casos de uso, elicitação, README Sprint 4.
- ADRs 0007/0008 (esqueleto) e scripts `06`/`07` para archive e v0.3.0.

## Test plan

- [x] Links locais nos novos Markdown
- [ ] CI Documentation
EOF
)"
