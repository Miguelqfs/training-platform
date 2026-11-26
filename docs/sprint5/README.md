# Sprint 5 — Command, Memento e desfazer

Fechamento integrado depois dos PRs de Artur (change), Luigi (Command), Davi
(persistência do Memento) e Miguel (desfazer na fachada e na API).

| Peça | Onde está |
| --- | --- |
| Change | [desfazer-atualizacao](../../openspec/changes/archive/2026-11-25-desfazer-atualizacao/proposal.md), arquivada no fechamento |
| Command | [ADR 0009](../adr/0009-fachada-command.md), `app/commands.py`, `app/facade.py` |
| Memento | [ADR 0010](../adr/0010-persistencia-memento.md), `Workout` / `WorkoutMemento` e repositórios |
| Contrato HTTP | [ADR 0011](../adr/0011-contrato-desfazer-treino.md), `POST /workouts/{id}/undo` |
| Caso de uso | [UC10](../04-casos-de-uso/UC10-desfazer-atualizacao.md) |
| Diagrama e padrões | [08-projeto.md](../08-projeto.md) |
| Arquitetura | [arquitetura.md](../arquitetura.md) |

Checklist da release: [fechamento-checklist.md](fechamento-checklist.md).

O desfazer restaura somente a última atualização, uma vez, nos dois modos de
armazenamento. Treinos diferentes não compartilham histórico. A exclusão apaga
o Memento. O evento `undo` entra no relatório HTML/PDF.
