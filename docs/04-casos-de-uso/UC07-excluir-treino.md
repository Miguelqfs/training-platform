# UC07 — Excluir treino

**Objetivo:** remover um plano de treino existente.
**Ator principal previsto:** Aluno; Administrador também pode operar o protótipo.
**Gatilho:** `DELETE /workouts/{id}`.
**Pré-condições de sucesso:** API iniciada e treino existente.
**Requisitos:** RF13, RF14, RF16; Sprint 4: RF19, RF20, RF23.
**Registro de evento:** [Luigi — guia Sprint 4](../sprint4/luigi-registro-acessos.md).

## Fluxo principal

1. O ator informa o ID do treino na URL.
2. A fronteira valida o ID; a fachada delega ao serviço.
3. O serviço obtém o proprietário (`user_id`) do treino.
4. Em transação compartilhada, remove o treino e grava evento `delete` para esse proprietário.
5. A API retorna 204 sem corpo.

## Alternativas e exceções

- **A1 — ID inválido (2):** 422; sem evento.
- **A2 — treino ausente ou segunda exclusão (4):** 404; sem evento novo.
- **E1 — falha na transação (4):** 503; treino e eventos como antes da requisição (RF23).

**Pós-condição de sucesso (Sprint 4):** treino removido e evento `delete` mantendo associação ao antigo proprietário.

**Garantia:** listagens (UC06) não geram eventos.

[Contrato completo](../../openspec/specs/treinos/spec.md) · [Índice](README.md)
