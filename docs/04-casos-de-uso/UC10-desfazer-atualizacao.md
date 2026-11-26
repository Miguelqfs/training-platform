# UC10 — Desfazer atualização de treino

**Objetivo:** restaurar nome e descrição imediatamente anteriores à última atualização bem-sucedida de um treino.
**Ator principal previsto:** Aluno; Administrador também pode operar o protótipo.
**Gatilho:** `POST /workouts/{id}/undo`.
**Pré-condições de sucesso:** API iniciada, treino existente e um estado anterior ainda não consumido.
**Requisitos:** RF24, RF25, RF26, RF27.
**Decisões:** [ADR 0009](../adr/0009-fachada-command.md), [ADR 0010](../adr/0010-persistencia-memento.md) e [ADR 0011](../adr/0011-contrato-desfazer-treino.md).

> A API não autentica o cliente. O evento `undo` fica associado ao **proprietário do treino**. Não há refazer.

## Fluxo principal

1. O ator informa o ID do treino. A requisição não tem corpo.
2. A fronteira exige ID inteiro positivo.
3. A fachada cria `UndoWorkoutCommand` e o executa com o contexto da aplicação.
4. Na mesma transação, o serviço lê o treino, consome o único Memento, restaura nome e descrição e grava um evento `undo` para o proprietário.
5. A API retorna 200 com `id`, `user_id`, `name` e `description`. Identificador e proprietário permanecem.

## Alternativas e exceções

- **A1 — treino nunca atualizado (4):** 409 `Nenhuma atualização disponível para desfazer`. O cadastro não cria Memento.
- **A2 — desfazer repetido (4):** o Memento já foi consumido. Novo 409, sem percorrer edições mais antigas e sem evento.
- **A3 — novo PUT depois do desfazer:** o `PUT` guarda outro estado anterior. O desfazer seguinte restaura somente esse estado. Ver [UC04](UC04-atualizar-treino.md).
- **A4 — outro treino:** o histórico do segundo treino não muda.
- **A5 — ID inválido (2):** 422; não é ausência de treino.
- **A6 — treino inexistente ou excluído (4):** 404 `Treino não encontrado`; a API não recria o treino.
- **A7 — PUT com os mesmos textos:** a atualização válida ainda substitui o Memento pelo estado anterior a ela, e esse estado pode ser desfeito.
- **A8 — PUT inválido:** 422 em [UC04](UC04-atualizar-treino.md); o Memento que já existia continua disponível.
- **A9 — duas requisições concorrentes:** no máximo uma restaura; a outra recebe 409. O Memento não é consumido duas vezes.
- **E1 — falha de gravação ou de commit (4):** 503 `Armazenamento de treinos indisponível`. Treino, Memento e eventos ficam como antes da requisição.

**Pós-condição de sucesso:** nome e descrição restaurados, Memento consumido e exatamente um evento `undo`. Não surge evento `update` adicional.

**Garantia:** falha do log auxiliar, depois do commit, não desfaz a restauração. RAM perde o Memento ao reiniciar a aplicação. SQLite mantém o Memento no arquivo até o desfazer ou a exclusão do treino. Bancos anteriores à Sprint 5 começam sem histórico.

**Exemplo:** depois de `PUT /workouts/1` com `{"name":"Costas","description":"remada"}`, `POST /workouts/1/undo` devolve o nome e a descrição que o treino tinha antes desse `PUT`.

[Contrato](../../openspec/specs/desfazer-atualizacao/spec.md) · [Índice](README.md)
