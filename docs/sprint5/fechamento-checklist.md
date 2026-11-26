# Checklist — fechamento Sprint 5 / v0.4.0

A implementação de desfazer está em `develop` (PR #27). Este fechamento cobre
documentação, validação, arquivamento e a release.

## 4.1 Documentação

- [x] Diagrama de classes com Command, Memento e repositório de estado anterior; PNG regenerado.
- [x] Diagrama de casos de uso com UC10; diagrama de exceções com 409.
- [x] Tabela de padrões em [08-projeto.md](../08-projeto.md) com Command e Memento e participantes reais.
- [x] [arquitetura.md](../arquitetura.md), casos de uso, README, glossário e visão alinhados ao código.
- [x] ADRs 0009 e 0010 descrevem o comando de desfazer e a integração no serviço.

## 4.2 Validação

Na raiz, com o ambiente de desenvolvimento:

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

Documentação:

```bash
npm install --prefix /tmp/training-platform-docs --no-save @fission-ai/openspec@1.14.3 yaml@2.8.2
DOCS_TOOLS_DIR=/tmp/training-platform-docs/node_modules node scripts/check-docs.mjs
node --test scripts/check-specs.test.mjs
```

- [x] Testes de desfazer em RAM e SQLite (`tests/test_workout_undo.py`).
- [x] CI do fechamento acompanhado no PR desta branch.

## 4.3 OpenSpec

Arquivar somente depois da validação local:

```bash
export DOCS_TOOLS_DIR=/tmp/training-platform-docs/node_modules
export PATH="$DOCS_TOOLS_DIR/.bin:$PATH"
openspec validate desfazer-atualizacao
openspec archive desfazer-atualizacao --yes
```

- [x] Itens 1.x–3.x e 4.1–4.3 da change marcados.
- [x] Specs em vigor com RF24–RF27 e relatório incluindo `undo`.

## 4.4 Release

Depois que este fechamento estiver em `develop` e o CI estiver verde:

```bash
bash scripts/rafael-git/10-release-v0.4.0.sh
```

- [ ] PR `develop` → `main` mergeado.
- [ ] Tag `v0.4.0` no commit da release.
- [ ] Checks da release passando.
