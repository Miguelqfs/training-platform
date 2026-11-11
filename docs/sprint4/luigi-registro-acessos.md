# Luigi — registro de acessos e Adapter

Referências: [design](../../openspec/changes/relatorio-de-acessos/design.md), [spec delta](../../openspec/changes/relatorio-de-acessos/specs/relatorio-de-acessos/spec.md), [ADR 0006](../adr/0006-repository-factory.md), esboço [ADR 0007](../adr/0007-adapter-log-eventos.md).

## Escopo do PR

- **tasks.md 2.1:** um evento por operação elegível bem-sucedida em UC03, UC04, UC05 e UC07.
- **tasks.md 2.2:** porta de log + Adapter (biblioteca à escolha, documentada no ADR).

Fora do escopo: listagens (UC06), relatório (UC09), alterar regras de treino já existentes.

## Modelo de evento

Usar [`AccessEvent`](../../app/accesses/domain.py):

- `user_id` = proprietário do treino no momento da operação (não identifica o cliente HTTP).
- `operation` ∈ `create` | `get` | `update` | `delete`.
- `occurred_at` em UTC via **relógio injetável** nos testes.

Nunca persistir ou logar senha, hash, e-mail ou corpo da requisição.

## Por operação

| UC | HTTP | Transação | Observação |
| --- | --- | --- | --- |
| UC03 create | `POST /workouts/` | `unit_of_work.transaction()` | Treino + evento atômicos; falha → 503, nada confirmado |
| UC04 update | `PUT /workouts/{id}` | `unit_of_work.transaction()` | Idem |
| UC07 delete | `DELETE /workouts/{id}` | `unit_of_work.transaction()` | Ler `user_id` **antes** de apagar o treino |
| UC05 get | `GET /workouts/{id}` | Somente `accesses.add` após leitura válida | 200 só depois do evento; falha de registro → 503 |
| UC06 list | `GET /workouts/` | — | Sem evento |
| UC09 relatório | — | — | Sem evento |

Snippet de mutação (conforme ADR 0006):

```python
with context.repositories.unit_of_work.transaction() as tx:
    treino = tx.workouts.add(registro)  # ou update/delete conforme o caso
    tx.accesses.add(AccessEvent(treino.user_id, "create", relógio.agora()))
```

`ApplicationContext.repositories` já está disponível em [`create_app`](../../app/main.py).

## `WorkoutService`

Hoje o serviço recebe apenas repositórios de treino e usuário. Sugestão:

- Injetar `Repositories` ou `UnitOfWork` + `AccessEventRepository` + fornecedor de instante UTC.
- Manter validações existentes; registrar evento só após regras de negócio satisfeitas.
- Propagar `PersistenceError` existente; mensagens públicas já tratadas em [`error_handlers`](../../app/error_handlers.py).

Rotas continuam passando pela fachada; não acumular lógica de evento na fronteira HTTP.

## Adapter de log

- **Porta** (ex.: `AccessLogPort`) com método que aceita só `user_id`, operação e instante.
- **Adapter** encapsula a biblioteca escolhida (stdlib `logging` ou outra — justificar no ADR 0007).
- Falha de log **não** altera status HTTP, não duplica/remove eventos e não registra dados sensíveis.
- Chamar o adapter após confirmar o evento no repositório (ou na mesma unidade lógica de sucesso, sem recursão em caso de erro do log).

## Testes mínimos

- Cada operação elegível gera exatamente um evento consultável (`list_between`).
- Listagem, 422, 404 e falhas anteriores à persistência: nenhum evento novo.
- RAM e SQLite: commit conjunto e rollback em falha simulada de treino ou evento.
- `get`: 503 se `accesses.add` falhar; treino já lido não deve “suceder” sem evento.
- Adapter: substituto que falha não muda resposta; nenhum campo sensível no teste duplo do log.

## Ao abrir o PR

- [ ] Marcar `tasks.md` 2.1 e 2.2.
- [ ] Completar [ADR 0007](../adr/0007-adapter-log-eventos.md).
- [ ] Base: `develop`.
