#!/usr/bin/env bash
set -euo pipefail
# Rodar após Luigi + Miguel em develop. Ajuste ARCHIVE_DATE se necessário.
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
ARCHIVE_DATE="${ARCHIVE_DATE:-2026-11-11}"
if [[ -z "${DOCS_TOOLS_DIR:-}" ]]; then
  echo "Defina DOCS_TOOLS_DIR (ver README) antes de arquivar." >&2
  exit 1
fi
export PATH="${DOCS_TOOLS_DIR}/.bin:${PATH}"
openspec validate relatorio-de-acessos
openspec archive relatorio-de-acessos --yes
git add openspec/
git commit -m "$(cat <<EOF
docs(openspec): arquivar change relatorio-de-acessos

Encerramento da Sprint 4 após implementação e validação integrada.
EOF
)"
echo "Revise openspec/changes/archive/${ARCHIVE_DATE}-relatorio-de-acessos e envie com git push."
