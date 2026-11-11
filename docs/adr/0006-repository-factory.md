# ADR 0006: Repository e Abstract Factory para persistência

## Contexto

Usuários e treinos já são acessados por protocolos com implementações em RAM e SQLite. Eventos de acesso precisam da mesma seleção de armazenamento. O registro futuro de um evento junto a uma mutação de treino exige uma transação compartilhada.

## Decisão

`RepositoryFactory` define a criação de uma família de repositórios e de uma unidade de trabalho. `MemoryRepositoryFactory` e `SQLiteRepositoryFactory` são fábricas concretas; a composição seleciona uma delas com a configuração existente. Os protocolos `UserRepository`, `WorkoutRepository` e `AccessEventRepository` representam os contratos utilizados pelo negócio. O conjunto é criado por aplicação, sem estado global.

`UnitOfWork.transaction()` fornece repositórios de treinos e eventos que compartilham o mesmo limite transacional. SQLite usa uma conexão e transação por operação; RAM usa uma trava compartilhada e cada repositório restaura seu próprio estado em caso de exceção. O chamador deve executar as duas escritas dentro do bloco e deixar exceções saírem dele. O registro dos eventos nas operações será integrado em outra tarefa.

Eventos têm proprietário, operação e instante UTC; consultas usam intervalo semiaberto. A tabela e o índice são criados sem modificar os dados existentes. A fábrica mantém as variáveis `USER_STORAGE` e `USER_DATABASE`, e aplicações SQLite para um mesmo arquivo compartilham dados confirmados.

## Consequências

A implementação isola a seleção de persistência e permite testes em ambos os modos. O escopo transacional precisa ser respeitado pelos serviços; capturar uma falha dentro do bloco pode confirmar escritas parciais. Aplicações em memória permanecem independentes. O repositório de eventos é a fonte dos relatórios; não cria eventos retroativos.

Os contratos de repositório ficam nos módulos `ports` das respectivas entidades; os módulos `repository` mantêm os nomes anteriores disponíveis para compatibilidade. O serviço que registrar uma operação poderá usar, por exemplo:

```python
with repositories.unit_of_work.transaction() as tx:
    treino = tx.workouts.add(registro)
    tx.accesses.add(evento)
```

O serviço deve validar os dados, identificar o proprietário e construir o evento antes de retornar sucesso; a fábrica não captura operações automaticamente. O contrato HTTP e os demais detalhes da geração de relatórios continuam na change proposta.

A entidade `AccessEvent` valida os campos e normaliza o instante; a regra de intervalo pertence ao domínio de acessos. A interface da unidade de trabalho fica em `app/unit_of_work.py`, sem dependência de SQLite ou implementações concretas.
