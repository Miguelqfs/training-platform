# Checklist — fechamento Sprint 4 / v0.3.0

Executar **somente** após Luigi e Miguel integrados em `develop`.

## 4.1 Documentação

- [ ] Remover caixas “planejado” do [diagrama de classes](../diagramas/classes-analise-usuarios.puml) e regenerar [diagrama-de-classes.png](../diagramas/diagrama-de-classes.png).
- [ ] Atualizar tabela de padrões em [08-projeto.md](../08-projeto.md) (Adapter e Template Method com classes reais).
- [ ] Conferir [arquitetura.md](../arquitetura.md) sem arestas tracejadas de PR.
- [ ] README: seção Sprint 4 com endpoint de relatório **funcional**.
- [ ] Casos de uso: pós-condições de evento sem nota “pendente Luigi”.

## 4.2 Validação

Na raiz do repositório, com venv ativo:

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

Documentação (conforme README):

```bash
npm install --prefix /tmp/training-platform-docs --no-save @fission-ai/openspec@1.14.3 yaml@2.8.2
DOCS_TOOLS_DIR=/tmp/training-platform-docs/node_modules node scripts/check-docs.mjs
node --test scripts/check-specs.test.mjs
```

- [ ] Nenhuma credencial em logs de teste ou respostas.
- [ ] CI verde na última commit de `develop`.

## 4.3 OpenSpec

Rodar via script (ajuste a data se necessário):

```bash
bash scripts/rafael-git/06-archive-openspec-change.sh
```

- [ ] `tasks.md` da change com itens 1.x–3.x marcados.
- [ ] Specs em vigor atualizadas se o processo da disciplina exigir delta arquivado em `openspec/specs/`.

## 4.4 Release

```bash
bash scripts/rafael-git/07-release-v0.3.0.sh
```

- [ ] PR `develop` → `main` mergeado.
- [ ] Tag `v0.3.0` no commit acordado pela equipe.
- [ ] Checks da release passando.
