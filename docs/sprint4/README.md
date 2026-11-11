# Sprint 4 — handoff e fechamento

Integração da change [relatorio-de-acessos](../../openspec/changes/relatorio-de-acessos/proposal.md).
Este índice orienta Luigi, Miguel e o fechamento da release **v0.3.0**.

## Estado das entregas

| Entrega | Responsável | Situação |
| --- | --- | --- |
| OpenSpec e design | Artur | Integrado (#16) |
| Repository, Factory, UoW, repos de eventos | Davi | Integrado (#17) |
| Projeto, arquitetura e diagrama (parcial) | Rafael | Integrado (#19) |
| Registro nas operações + Adapter | Luigi | Implementado neste PR; aguardando revisão e integração |
| Template Method + HTML/PDF + API relatório | Miguel | Pendente |
| UCs, elicitação, archive, release | Rafael | Parcial — ver [fechamento-checklist](fechamento-checklist.md) |

## Guias de implementação

- [Luigi — registro de eventos e Adapter](luigi-registro-acessos.md)
- [Miguel — relatório e Template Method](miguel-relatorio.md)
- [Checklist pós-integração e v0.3.0](fechamento-checklist.md)

## Ordem sugerida de merge

1. Luigi em `develop` (ADR 0007 preenchido no PR).
2. Miguel em `develop` (ADR 0008 / contratos públicos no PR).
3. Rafael: remover participantes “planejado” do [diagrama](../diagramas/classes-analise-usuarios.puml), executar [fechamento-checklist](fechamento-checklist.md), arquivar change, PR `develop` → `main` com tag `v0.3.0`.

Commits e merges do Rafael usam scripts em [`scripts/rafael-git/`](../../scripts/rafael-git/) (não rodar `git commit` solto no harness).
