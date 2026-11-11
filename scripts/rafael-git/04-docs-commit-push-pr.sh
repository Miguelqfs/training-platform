#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
git fetch origin develop
git checkout -B docs/sprint4-projeto-rafael origin/develop
git add docs/08-projeto.md docs/arquitetura.md docs/diagramas/classes-analise-usuarios.puml docs/diagramas/diagrama-de-classes.png scripts/rafael-git/
git commit -m "$(cat <<'EOF'
docs(sprint4): atualizar projeto, arquitetura e diagrama de classes

Documenta Repository, Abstract Factory e Unit of Work após integração dos
repositórios de eventos; mantém Adapter e Template Method como entregas pendentes.
EOF
)"
git push -u origin docs/sprint4-projeto-rafael
gh pr create --base develop --head docs/sprint4-projeto-rafael --title "docs(sprint4): projeto, arquitetura e diagrama de classes" --body "$(cat <<'EOF'
## Resumo

Atualiza `docs/08-projeto.md`, `docs/arquitetura.md` e o diagrama PlantUML/PNG para o estado após a fábrica de repositórios e eventos de acesso. Participantes ainda não implementados (Adapter, relatório) ficam indicados no diagrama até os PRs de Luigi e Miguel.

## Test plan

- [x] PNG gerado a partir do `.puml`
- [ ] `node scripts/check-docs.mjs` após merge com `develop`
EOF
)"
