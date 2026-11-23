# ADR 0009: Fachada baseada em Command

## Status

Aceito na implementação de Luigi para a Sprint 5; sujeito à revisão do PR.
Cobre as tarefas **3.1** e **3.2** da change
[desfazer-atualizacao](../../openspec/changes/desfazer-atualizacao/tasks.md),
exceto o comando de desfazer, que acompanha a implementação do Memento.

## Contexto

O [checklist da Sprint 5](https://github.com/rkulesza/mps-modelo/blob/main/docs/00-entregas.md)
pede uma fachada de negócio baseada em Command. Até a Sprint 4,
`FacadeSingletonController` chamava diretamente os serviços do contexto
([ADR 0005](0005-treinos-fachada.md), [ADR 0008](0008-relatorio-template-method.md)).
O [design da change](../../openspec/changes/desfazer-atualizacao/design.md) exige
preservar as assinaturas da fachada, o Singleton sem dados e o contexto por
aplicação, e encaminhar também o futuro desfazer por um comando.

## Decisão

Participantes do Command:

| Papel | Participante e responsabilidade |
| --- | --- |
| Client | Rotas FastAPI e métodos públicos da fachada, que criam o comando com os argumentos da requisição. |
| Command | Protocolo `Command[Result]` em `app/commands.py`, com `execute(context) -> Result`. |
| ConcreteCommand | `RegisterUserCommand`, `ListUsersCommand`, `CreateWorkoutCommand`, `GetWorkoutCommand`, `ListWorkoutsCommand`, `UpdateWorkoutCommand`, `DeleteWorkoutCommand`, `CountEntitiesCommand` e `GenerateAccessReportCommand`. |
| Invoker | `FacadeSingletonController.execute(context, command)`. |
| Receiver | `UserService`, `WorkoutService` e `AccessReportService` do `ApplicationContext` recebido. |

Cada comando é uma dataclass congelada que guarda somente os argumentos da
operação, como IDs, DTOs de cadastro ou atualização e solicitação de relatório.
O contexto não é atributo do comando: ele é passado em `execute`, para que o mesmo
comando rode em qualquer aplicação sem fixar armazenamento e sem estado global.
Comandos não validam regras, não acessam repositórios nem SQL; delegam ao
serviço, que continua responsável por validação, unidade de trabalho e eventos.

Os métodos públicos da fachada (`register_user`, `list_users`, `create_workout`,
`get_workout`, `list_workouts`, `update_workout`, `delete_workout`,
`count_entities` e `generate_access_report`) mantêm nomes, parâmetros e retornos.
Cada um cria o comando correspondente e chama `execute`. As rotas não mudam, e
os contratos HTTP, códigos de status, mensagens e OpenAPI permanecem idênticos.
Exceções de domínio e de persistência atravessam o comando sem tradução.

`ApplicationContext` passa para `app/context.py`, evitando import circular entre
fachada e comandos; `app.facade` o reexporta para compatibilidade de imports.
O Singleton, a trava de construção e a ausência de atributos de instância seguem
como no ADR 0005.

O desfazer da change `desfazer-atualizacao` será um novo comando concreto,
delegando ao serviço de treinos e exposto por um método próprio da fachada. A
captura e restauração do estado anterior pertencem ao Memento e à unidade de
trabalho, não ao comando, que não mantém histórico.

## Alternativas consideradas

- **Comando com contexto no construtor:** reduziria um parâmetro de `execute`, mas
  acoplaria cada instância a uma aplicação e facilitaria reutilizá-la no contexto errado.
- **Comandos com `undo()` próprio:** é a variante clássica de desfazer com Command,
  mas exigiria guardar histórico em memória do processo, quebrando o isolamento
  por aplicação e a persistência SQLite. A change escolheu Memento no armazenamento.
- **Rotas criando comandos e chamando apenas `execute`:** mudaria os pontos de
  extensão já testados das rotas (substituição dos métodos da fachada) sem ganho
  para o cliente HTTP.
- **Fila ou histórico de comandos:** não há requisito de auditoria, repetição ou
  execução assíncrona; os eventos de acesso já registram o uso.

## Consequências

Novas operações exigem um comando e um método na fachada, sem alterar o invoker.
O acréscimo de uma camada de objetos tem custo desprezível em relação a HTTP e I/O.
`tests/test_commands.py` verifica que cada método da fachada cria o comando
esperado, que cada comando delega somente ao serviço correto do contexto recebido,
a imutabilidade dos comandos, a propagação de erros e o isolamento de contextos em
RAM e SQLite. `tests/test_facade.py` continua cobrindo as rotas, o Singleton e o
isolamento de aplicações.
