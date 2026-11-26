#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
git add \
  README.md \
  docs \
  openspec \
  scripts/rafael-git/10-release-v0.4.0.sh \
  scripts/rafael-git/11-sprint5-commit-push-pr.sh
git commit -m "$(cat <<'EOF'
docs(sprint5): fechar Command, Memento e o desfazer

Atualiza diagrama, padrões, arquitetura, casos de uso e README para as
classes reais e arquiva a change desfazer-atualizacao.

EOF
)"
git push -u origin HEAD:docs/sprint5-fechamento
gh pr create --base develop --head docs/sprint5-fechamento --title "docs(sprint5): fechar Command, Memento e o desfazer" --body "$(cat <<'EOF'
## Resumo

- Atualiza o diagrama de classes, os casos de uso, a tabela de padrões, a arquitetura e o README para Command, Memento e `POST /workouts/{id}/undo`.
- Arquiva a change `desfazer-atualizacao`. As specs em vigor passam a incluir RF24–RF27, e o relatório conta a operação `undo`.
- A tag `v0.4.0` fica para o PR `develop` → `main`, depois deste merge.

## Test plan

- [x] 456 testes aprovados, incluindo desfazer em RAM e SQLite
- [x] Ruff e formatação
- [x] `scripts/check-docs.mjs` e `scripts/check-specs.test.mjs`
- [ ] CI deste PR
- [ ] Depois do merge: `bash scripts/rafael-git/10-release-v0.4.0.sh`

EOF
)"
