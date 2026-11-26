# ADR 0010: Persistência do Memento na unidade de trabalho

## Status

Aceito. Cobre a persistência do Memento da Sprint 5. A operação de desfazer
que consome esse estado está no [ADR 0011](0011-contrato-desfazer-treino.md).
A change está em
[desfazer-atualizacao](../../openspec/changes/archive/2026-11-25-desfazer-atualizacao/tasks.md).

## Contexto

O [design da change](../../openspec/changes/archive/2026-11-25-desfazer-atualizacao/design.md) e os
requisitos [RF24–RF26](../../openspec/specs/desfazer-atualizacao/spec.md)
exigem guardar no máximo um estado anterior (`name` e `description`) por treino a
cada atualização bem-sucedida, restaurá-lo uma única vez ao desfazer e tratar
alteração do treino, Memento e evento de acesso como uma unidade atômica nos
modos RAM e SQLite. Bancos SQLite existentes devem continuar funcionando sem
perder dados nem fabricar histórico retroativo.

Os [ADRs 0006](0006-repository-factory.md), [0007](0007-adapter-log-eventos.md)
e [0009](0009-fachada-command.md) definem a seleção por fábrica, o isolamento por
aplicação e o uso de Command na fachada. O serviço, a rota e o evento `undo`
foram integrados em seguida e estão registrados no
[ADR 0011](0011-contrato-desfazer-treino.md).

## Decisão

Participantes do Memento e da persistência transacional:

| Papel | Participante e responsabilidade |
| --- | --- |
| Originator | `Workout` em `app/workouts/domain.py`: cria `WorkoutMemento` (`create_memento`) e gera nova instância restaurada preservando `id` e `user_id` (`restore`). |
| Memento | `WorkoutMemento` em `app/workouts/domain.py`: dataclass congelada com `name` e `description`, validação dos limites da política de treinos e conversão `to_update`. |
| Caretaker / Porta | `WorkoutMementoRepository` em `app/workouts/ports.py`: contrato `save`, `get`, `consume` e `delete`, reexportado em `app/workouts/repository.py`. |
| Persistência | `MemoryWorkoutMementoRepository` e `SQLiteWorkoutMementoRepository` em `app/workouts/repository.py`. |
| Transação | `UnitOfWork` e `TransactionRepositories` em `app/unit_of_work.py`; implementações `MemoryUnitOfWork` e `SQLiteUnitOfWork` em `app/repositories.py`. |

### Contratos de domínio e repositório

`WorkoutMemento` armazena somente os campos restauráveis (`name` e `description`)
e valida tipos e limites da política de treinos na construção. `Workout` é
imutável: `create_memento()` captura o estado atual sem expor identidade nem
propriedade; `restore(memento)` devolve um novo `Workout` com `id` e `user_id`
preservados.

`WorkoutMementoRepository` expõe quatro operações:

- `save(workout_id, memento)`: grava ou substitui o único Memento associado ao treino.
- `get(workout_id)`: consulta o Memento sem consumi-lo; retorna `None` quando ausente.
- `consume(workout_id)`: remove e retorna o Memento atomicamente em uma operação, ou `None` quando ausente.
- `delete(workout_id)`: remove o Memento do treino, retornando `True` se existia.

Em RAM, `MemoryWorkoutMementoRepository` armazena `dict[int, WorkoutMemento]`
protegido pela mesma `RLock` da aplicação e restaura uma cópia no rollback de
`MemoryUnitOfWork`. IDs inválidos (incluindo `bool`, já que `bool` herda de `int`
em Python) lançam `InvalidWorkoutError` em `save` e retornam vazio em leituras e
remoções, sem colidir com IDs reais.

### Esquema SQLite e compatibilidade com bancos existentes

`SQLiteWorkoutMementoRepository` cria a tabela abaixo apenas quando ausente:

```sql
CREATE TABLE IF NOT EXISTS workout_mementos (
    workout_id INTEGER PRIMARY KEY REFERENCES workouts(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT ''
)
```

- **Compatibilidade retroativa:** bancos anteriores à Sprint 5 mantêm usuários,
  treinos e eventos intactos e iniciam com `workout_mementos` vazia, sem
  fabricar histórico.
- **Substituição única:** `save` usa `INSERT ... ON CONFLICT(workout_id) DO UPDATE`,
  mantendo no máximo um Memento por treino mesmo quando os campos repetem os atuais.
- **Consumo atômico:** `consume` usa `DELETE ... WHERE workout_id = ? RETURNING name, description`
  com leitura integral do cursor (`fetchall`), impedindo consumo duplo ou
  estado parcial.
- **Exclusão em cascata:** `ON DELETE CASCADE` remove o Memento automaticamente
  quando o treino é excluído em SQLite, além de `delete` explícito dentro da UoW.
- **IDs arbitrariamente grandes:** todas as consultas usam `str(workout_id)` no
  binding SQLite; `SQLITE_CONSTRAINT_FOREIGNKEY` e `SQLITE_MISMATCH` em `save`
  são traduzidos para `WorkoutNotFoundError`, e os demais erros SQLite para
  `PersistenceError` com `public_message = PersistenceError.WORKOUT_MESSAGE`.

### Unidade de trabalho e serialização concorrente

`TransactionRepositories` passa a expor `mementos: WorkoutMementoRepository` ao
lado de `workouts` e `accesses`, e `Repositories` inclui `mementos` criado pelas
fábricas `MemoryRepositoryFactory` e `SQLiteRepositoryFactory`.

`SQLiteUnitOfWork.transaction()` inicia transações com `BEGIN IMMEDIATE` antes de
qualquer leitura. Assim, atualizações, exclusões e desfazer concorrentes sobre o
mesmo treino serializam desde o início da transação usando o timeout do driver,
evitando leitura obsoleta antes de adquirir trava de escrita e evitando falha de
promoção `SHARED -> RESERVED`.

Nos PRs seguintes, `WorkoutService` poderá coordenar captura e consumo no mesmo
bloco transacional dos treinos e eventos:

```python
with self._transaction() as tx:
    current = tx.workouts.get_by_id(workout_id)
    if current is None:
        raise WorkoutNotFoundError()
    tx.mementos.save(workout_id, current.create_memento())
    workout = tx.workouts.update(workout_id, fields)
    event = self._record(tx, workout, "update")
```

E ao desfazer:

```python
with self._transaction() as tx:
    current = tx.workouts.get_by_id(workout_id)
    if current is None:
        raise WorkoutNotFoundError()
    memento = tx.mementos.consume(workout_id)
    if memento is None:
        raise WorkoutUndoUnavailableError()
    restored = current.restore(memento)
    workout = tx.workouts.update(workout_id, restored.create_memento().to_update())
    event = self._record(tx, workout, "undo")
```

## Alternativas consideradas

- **Colunas anuláveis na tabela `workouts`:** acoplaria o esquema da entidade
  principal ao histórico opcional e misturaria metadados de undo às consultas
  regulares de treinos. Tabela dedicada com chave primária e FK em cascata isola
  a responsabilidade e preserva bancos legados sem `ALTER TABLE`.
- **Histórico em memória nos comandos ou na fachada:** violaria o isolamento por
  aplicação ([ADR 0009](0009-fachada-command.md)) e perderia o estado anterior
  ao reiniciar o SQLite.
- **Manter `BEGIN` (`DEFERRED`) na `SQLiteUnitOfWork`:** permitiria duas
  transações lerem o mesmo treino ou Memento antes da escrita, causando conflito
  de promoção de trava ou risco de restauração obsoleta sob concorrência.
- **Pilha com múltiplos níveis de histórico:** fora do escopo da change, que
  determina no máximo um Memento por treino e consumo único ao desfazer.

## Consequências

- A mudança em `TransactionRepositories` e `Repositories` exige que stubs de
  teste que constroem `TransactionRepositories` diretamente forneçam um
  repositório de Mementos (atualizado em `tests/test_workout_domain.py`).
- RAM permanece isolado por instância de aplicação e volátil entre reinícios;
  SQLite compartilha estado confirmado entre instâncias apontadas para o mesmo
  arquivo e isola arquivos distintos.
- `tests/test_workout_memento_persistence.py` cobre contratos do Memento,
  ciclo de vida em RAM e SQLite, bancos legados, exclusão em cascata, rollback
  de captura/substituição/consumo/remoção, falhas de commit/trava e
  serializabilidade concorrente.
- `WorkoutService` captura o Memento no `PUT`, consome na restauração e remove
  na exclusão, na mesma transação do treino e do evento. A restauração grava os
  campos restaurados sem chamar a operação pública de atualização. O contrato
  HTTP e o evento `undo` estão no [ADR 0011](0011-contrato-desfazer-treino.md).
