# UC05 — Consultar treino

**Objetivo:** obter um plano de treino pelo identificador.
**Ator principal previsto:** Aluno; Administrador também pode operar o protótipo.
**Gatilho:** `GET /workouts/{id}`.
**Pré-condições de sucesso:** API iniciada e treino existente.
**Requisitos:** RF10, RF16; a partir da Sprint 4 também RF19, RF20, RF23 (registro do evento `get`).
**Registro de evento:** [Luigi — guia Sprint 4](../sprint4/luigi-registro-acessos.md).

## Fluxo principal

1. O ator informa o ID do treino na URL.
2. A fronteira valida inteiro JSON positivo; a fachada delega ao serviço.
3. O repositório localiza o treino.
4. Após confirmação do treino, o serviço persiste um evento `get` associado ao `user_id` proprietário.
5. A API retorna 200 com os quatro campos públicos.

## Alternativas e exceções

- **A1 — ID inválido (2):** 422; sem evento.
- **A2 — treino ausente (3):** 404; sem evento.
- **E1 — persistência do treino (3):** 503; sem evento.
- **E2 — falha ao registrar evento após leitura válida (4):** 503; nenhum evento confirmado (RF23).

**Pós-condição de sucesso (Sprint 4):** resposta 200 e um evento `get` consultável para o proprietário, sem senha, hash, e-mail ou corpo HTTP no evento.

**Garantia em falha:** treino e eventos anteriores preservados.

[Contrato completo](../../openspec/specs/treinos/spec.md) · [Índice](README.md)
