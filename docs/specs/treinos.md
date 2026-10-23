# Treinos e fachada: Sprint 3

A especificação normativa está em [treinos](../../openspec/specs/treinos/spec.md)
e [fachada](../../openspec/specs/fachada/spec.md). A origem dos limites e da
interpretação da contagem está no [ADR 0005](../adr/0005-treinos-fachada.md).

| ID | Requisito | Prioridade |
| --- | --- | --- |
| RF08 | Cadastrar treino vinculado a usuário. | Essencial |
| RF09 | Validar campos, tipos e limites. | Essencial |
| RF10 | Consultar treino por ID. | Essencial |
| RF11 | Listar treinos em ordem de ID. | Essencial |
| RF12 | Substituir nome/descrição preservando ID e vínculo. | Essencial |
| RF13 | Excluir treino sem alterar usuários e outros treinos. | Essencial |
| RF14 | Gerar IDs crescentes sem reutilização após exclusões. | Essencial |
| RF15 | Usar RAM ou o mesmo SQLite dos usuários. | Essencial |
| RF16 | Executar operações pela fachada única. | Essencial |
| RF17 | Contar usuários e treinos. | Essencial |
| RF18 | Isolar contextos com uma fachada por processo. | Essencial |

Os [RNFs](../../openspec/specs/rnf/) cobrem indisponibilidade, atomicidade,
durabilidade, segurança das respostas e contratos substituíveis. Consulte os
[casos de uso](../04-casos-de-uso/README.md) para os fluxos.

Não há autenticação, autorização, exercícios, execução ou histórico nesta sprint.
