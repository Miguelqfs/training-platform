# ADR 0011 — Contrato de desfazer atualização de treino

## Contexto

Os requisitos RF24–RF27 da Sprint 5 definem o desfazer da última atualização
de um treino e o registro da operação no relatório de acessos. O
[ADR 0009](0009-fachada-command.md) define a execução via Command. O
[ADR 0010](0010-persistencia-memento.md) define a persistência do Memento.

## Decisão

`POST /workouts/{workout_id}/undo` recebe um ID inteiro positivo e dispensa
corpo. A fachada executa `UndoWorkoutCommand` com o contexto da aplicação.

| Status | Resposta |
| --- | --- |
| 200 | Treino restaurado com `id`, `user_id`, `name` e `description`. |
| 404 | Treino inexistente ou excluído. |
| 409 | Treino sem histórico. A mensagem é `Nenhuma atualização disponível para desfazer`. |
| 422 | ID inválido. |
| 503 | Armazenamento de treinos indisponível. |

Cada `PUT` bem-sucedido captura o estado anterior, inclusive quando os campos
recebidos são iguais aos atuais. A exclusão remove o Memento. Ao desfazer,
`WorkoutService` consome o Memento, restaura os campos e grava um único evento
`undo` com o proprietário do treino e o instante UTC. Treino, Memento e
evento compartilham a mesma transação. O log auxiliar roda após o commit.

Os relatórios HTML e PDF exibem `undo` como quinta operação, inclusive quando
a contagem é zero. Na primeira abertura de um SQLite legado, o repositório
recria a tabela de eventos em uma transação para ampliar o `CHECK` da
operação. A migração copia os eventos com seus IDs, preserva a referência a
usuários e recria o índice de intervalo. As aberturas seguintes usam a tabela
já migrada.

## Alternativas consideradas

- Reusar o endpoint de atualização confundiria a edição com o desfazer.
  Usar a rotina de atualização durante a restauração também geraria um novo
  Memento e um evento `update`.
- Uma tabela separada para eventos `undo` exigiria combinar duas fontes em
  cada consulta de relatório. A tabela atual mantém o filtro e a ordem dos
  eventos no mesmo repositório.

## Verificação

Os [testes de desfazer](../../tests/test_workout_undo.py) cobrem o contrato
HTTP, o consumo concorrente e a migração de um SQLite legado. Os
[testes de eventos](../../tests/test_access_recording.py) verificam rollback e
log após o commit. Os [testes de relatórios](../../tests/test_access_reports.py)
verificam a contagem em HTML e PDF.
