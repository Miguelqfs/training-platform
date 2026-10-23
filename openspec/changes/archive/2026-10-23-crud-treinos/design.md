# Design: crud-treinos

## Context

A API compõe a aplicação em `app/main.py`. Usuários seguem domínio, serviço, protocolo e implementações RAM e SQLite. `UserService` recebe `UserRepository`. `add_user` recebe `UserRegistration`. O repositório recebe `NewUser`, já com hash. `create_app` recebe `storage` e `database_path`. `USER_STORAGE` aceita `memory` e `sqlite`; `USER_DATABASE` informa o arquivo.

As rotas de usuários leem `app.state.user_service`. Não há fachada. O cadastro de usuários não remove registros, então o ID em RAM ainda usa o tamanho da coleção mais um. Treinos poderão ser excluídos; esse cálculo deixa de ser válido para eles.

Os testes criam aplicações independentes com `create_app`. Uma fachada que guarde repositórios em estado global faria essas aplicações compartilharem dados.

## Goals / Non-Goals

**Goals:**

- Cadastrar, consultar, listar, atualizar e excluir treinos ligados a um usuário existente.
- Oferecer os dois modos de persistência já selecionáveis, no mesmo arquivo SQLite quando esse modo estiver ativo.
- Fazer as rotas usarem uma `FacadeSingletonController` única no processo, com contexto próprio por aplicação e compartilhamento de dados somente quando o mesmo arquivo SQLite for configurado.
- Contar usuários e treinos a partir dos registros persistidos.
- Manter os contratos HTTP e de credenciais de usuários.

**Non-Goals:**

- Autenticação, autorização, aplicativo, agente de IA, exercícios, histórico e exclusão de usuários.
- Padrões previstos para as Sprints 4 e 5.
- Troca de linguagem, framework, banco ou organização do repositório.

## Decisions

### 1. Treino é um plano, não uma sessão executada

`Workout` tem `id`, `user_id`, `name` e `description`. Um usuário possui zero ou mais treinos. Cada treino referencia exatamente um usuário, pelo ID já persistido na mesma aplicação. Não existe coleção paralela de usuários.

| Campo | Regra proposta |
| --- | --- |
| `id` | Inteiro maior ou igual a 1, gerado pelo armazenamento. Imutável. |
| `user_id` | Inteiro maior ou igual a 1 e ID de usuário existente. Imutável. |
| `name` | Obrigatório. Espaços externos são removidos. De 1 a 100 caracteres Unicode depois disso. |
| `description` | Texto opcional. Campo omitido vira `""`; `null` e valores não textuais são recusados. Espaços externos são removidos. No máximo 1.000 caracteres. Texto só com espaços fica vazio e é aceito. |

Os limites ficam em constantes de `app/workouts/policy.py`: `MIN_WORKOUT_NAME_LENGTH = 1`, `MAX_WORKOUT_NAME_LENGTH = 100` e `MAX_WORKOUT_DESCRIPTION_LENGTH = 1_000`. O tamanho é `len` da string já normalizada.

Nomes podem se repetir, no mesmo usuário ou em usuários diferentes. Não há 409 para treino.

`id` e `user_id` não entram no corpo de `PUT`. Enviar qualquer um deles, ou outro campo desconhecido, é 422. O treino anterior permanece. A omissão de `description` no `PUT` grava `""`; a atualização substitui os dois campos mutáveis.

A entrada HTTP usa `extra="forbid"`. O `user_id` no corpo é inteiro estrito: texto, booleanos, floats e `null` são recusados. `name` é texto obrigatório no cadastro e na atualização. O `POST` recusa `id`; o `PUT` recusa `id` e `user_id` mesmo que repitam valores existentes. Os esquemas de usuários continuam com o comportamento atual.

Objetos de domínio, no mesmo estilo de usuários:

- `WorkoutRegistration`: `user_id`, `name`, `description`.
- `WorkoutUpdate`: `name`, `description`.
- `Workout`: os quatro campos, dataclass congelada.

O serviço normaliza e valida. O repositório recebe os valores já aceitos. No cadastro direto ao serviço, valida-se tipo/valor de `user_id`, depois nome e descrição; só depois se consulta a existência do usuário. Na atualização, validam-se ID de destino, nome e descrição antes da busca do treino. Cada exceção de domínio informa somente a primeira regra violada. A fronteira HTTP pode reportar vários erros de campos distintos, sem exigir essa ordem.

Mensagens de domínio:

- `Nome do treino deve ter de 1 a 100 caracteres`
- `Descrição do treino deve ter no máximo 1000 caracteres`
- `ID do usuário deve ser um inteiro positivo`
- `ID do treino deve ser um inteiro positivo`
- `Usuário não encontrado`
- `Treino não encontrado`

Na fronteira HTTP, tamanho, tipo, obrigatoriedade e campo desconhecido usam o esquema. A resposta 422 identifica o campo em `loc` e a regra em `type` ou `msg`, sem as chaves `input` e `ctx`. Ausência do usuário ou do treino usa as mensagens acima com 404.

Os esquemas públicos retornam somente os campos previstos. Os textos de nome e descrição não são comparados à senha do usuário nem censurados quando coincidem com ela; a proteção de credenciais impede serialização indevida do usuário e reprodução da entrada sensível nos erros.

### 2. IDs não voltam a ser usados depois da exclusão

Em RAM, `MemoryWorkoutRepository` guarda `next_id`, iniciado em 1. Cada inclusão consome o valor e incrementa o contador dentro do mesmo `Lock` das demais mutações. A exclusão não reduz o contador. O ID não é `len(coleção) + 1`.

Em SQLite, `id INTEGER PRIMARY KEY AUTOINCREMENT`. Sem `AUTOINCREMENT`, o SQLite pode reutilizar o maior rowid já removido.

A não reutilização se refere a cadastros confirmados. Não se exige ausência de lacunas nem impedir reutilização de IDs internos de uma transação revertida. Em RAM, o contador pertence àquela coleção e recomeça em uma aplicação nova.

O ID de usuário em RAM permanece como está. Aquela coleção não remove elementos nesta sprint. Alterá-la não é necessário para o CRUD de treinos.

### 3. Os dois modos usam a seleção já existente

Não há `WORKOUT_STORAGE`. A composição resolve `storage` e caminho uma única vez por aplicação, respeitando os argumentos explícitos antes das variáveis de ambiente e preservando o valor padrão atual. Ela cria primeiro o repositório de usuários e depois o de treinos com essa mesma configuração resolvida. Os serviços de um contexto recebem exatamente esses repositórios; não se cria uma segunda coleção RAM de usuários para validar vínculos.

A tabela nova é criada com `CREATE TABLE IF NOT EXISTS`. A tabela `users` não é apagada nem recriada. Um banco legado com usuários e sem `workouts` passa a ter a tabela nova vazia e conserva os usuários. Se `workouts` já existir, seus dados e a sequência de IDs são preservados.

```sql
CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (user_id) REFERENCES users (id)
)
```

Não há `CHECK` de tamanho no SQL. Os limites ficam nas constantes Python, para não duplicar números nem transformar erro de validação em falha de banco.

Cada conexão usada por usuários e por treinos executa `PRAGMA foreign_keys = ON` antes de outras operações. A opção vale por conexão. As escritas continuam parametrizadas e transacionais, como o cadastro de usuários: sucesso confirma e exceção reverte.

A chave estrangeira é integridade adicional. O serviço consulta `UserRepository.get_by_id` antes de gravar. Se o usuário não existe, responde 404 e não insere. Se a chave estrangeira falhar mesmo assim, a tradução também é 404 com `Usuário não encontrado`, não 503.

Essa tradução reconhece especificamente `SQLITE_CONSTRAINT_FOREIGNKEY`; não converte todo `IntegrityError` em usuário ausente. Erros de outras restrições não se passam por HTTP 404.

`sqlite3.Error` de leitura ou escrita, fora unicidade de usuário e chave estrangeira de treino, continua virando `PersistenceError`. A mensagem interna não vai para o cliente. O handler passa a publicar `public_message`, com o texto atual como padrão:

- usuários: `Armazenamento de usuários indisponível`
- treinos: `Armazenamento de treinos indisponível`

Assim NF-CON-01 permanece verdadeiro. Diretório inexistente ou arquivo que não é um banco SQLite continua falhando na inicialização com `PersistenceError`, antes de atender requisições. `create_app` não captura essa exceção.

O contrato de `PersistenceError` é introduzido junto ao primeiro repositório que o utiliza, preservando as chamadas antigas e a causa original. `public_message` recebe somente as constantes públicas definidas para usuários e treinos; não recebe `str(sqlite_error)`, SQL, caminho ou texto enviado pelo cliente. Se a busca do usuário falha durante cadastro de treino, `WorkoutService` preserva a causa e converte a mensagem pública para a de treinos. Ausência real do usuário continua sendo erro de negócio 404.

Criação, atualização e exclusão usam transações até o término da operação. Testes com gatilhos que abortam `INSERT`, `UPDATE` e `DELETE` verificam, para cada mutação, o estado completo anterior e a contagem, tanto no banco quanto na API. Após remover a falha injetada, a mesma operação deve funcionar sem efeitos duplicados.

A listagem de treinos sai ordenada por `id` crescente nos dois repositórios. Não há filtro por usuário nem paginação.

Contratos de repositório propostos:

```text
UserRepository
    add(data: NewUser) -> User                       # contrato existente
    list_users() -> list[User]                       # contrato existente
    get_by_id(user_id: int) -> User | None
    count() -> int

WorkoutRepository
    add(data: WorkoutRegistration) -> Workout
    get_by_id(workout_id: int) -> Workout | None
    list_workouts() -> list[Workout]
    update(workout_id: int, data: WorkoutUpdate) -> Workout | None
    delete(workout_id: int) -> bool
    count() -> int
```

`None` em busca/atualização e `False` em exclusão significam registro inexistente, nunca falha de banco. Os serviços traduzem esses resultados para exceções de domínio. Repositórios retornam registros completos, sem alterar os DTOs congelados recebidos. Os métodos antigos de usuários conservam assinaturas e comportamento.

### 4. A fachada é única; os dados pertencem à aplicação

Classes em `app/facade.py`:

```text
ApplicationContext
    users: UserService
    workouts: WorkoutService

FacadeSingletonController
    get_instance() -> FacadeSingletonController
    register_user(context, registration) -> User
    list_users(context) -> list[User]
    create_workout(context, registration) -> Workout
    get_workout(context, workout_id) -> Workout
    list_workouts(context) -> list[Workout]
    update_workout(context, workout_id, update) -> Workout
    delete_workout(context, workout_id) -> None
    count_entities(context) -> int
```

`count_entities` retorna `context.users.count_users() + context.workouts.count_workouts()`. O resultado é um inteiro. A rota `GET /statistics/entities` o embrulha em `{"total": N}`. Não há contador global separado dos repositórios. Usuários `student` e `admin` entram na soma. Exclusão concluída reduz o total. Atualização o mantém. Operação rejeitada não o altera.

A contagem corresponde às operações confirmadas nos cenários sequenciais descritos. Não se promete uma fotografia transacional única entre duas consultas concorrentes; esta sprint não introduz travas globais nem um mecanismo distribuído para isso.

O escopo do Singleton é o processo Python. `__new__` usa trava de classe e verificação dupla. `FacadeSingletonController()` e `get_instance()` devolvem o mesmo objeto, também quando as primeiras chamadas concorrem. Nova chamada devolve a instância já criada. A instância não recebe repositório, caminho, usuário, treino nem contexto no construtor.

`create_app` monta um `ApplicationContext` imutável quanto às referências dos serviços e o guarda em `app.state.context`. Não substitui a fachada. As rotas obtêm o contexto de `request.app` e chamam `FacadeSingletonController.get_instance()`. Validação, SQL e coleções continuam nos serviços e repositórios.

Cada aplicação tem seu contexto. RAM usa coleções independentes; arquivos SQLite diferentes usam dados independentes. Duas aplicações ativas configuradas com o mesmo arquivo SQLite compartilham intencionalmente os registros confirmados, mantendo suas próprias referências de contexto. Criar a segunda aplicação não esvazia o arquivo nem redireciona as dependências da primeira.

O teste da primeira construção concorrente roda em um subprocesso novo para garantir uma instância ainda não criada, sem depender da ordem da suíte nem adicionar um método de reset à API de produção. Testes de operações podem substituir métodos temporariamente, com restauração automática, sem acumular dados no Singleton.

`WorkoutService` recebe `WorkoutRepository` e `UserRepository`. Não referencia as classes concretas, não abre SQL e não chama a API HTTP. `UserService` também permanece ligado só ao protocolo.

Alternativas recusadas:

- Guardar os repositórios na fachada global. Aplicações criadas no mesmo processo passariam a compartilhar dados.
- Recriar a fachada dentro de `create_app`. A segunda aplicação apagaria o vínculo da primeira e a identidade única deixaria de ser estável.
- Considerar uma atribuição em `app.state` suficiente para demonstrar Singleton. Isso isola os dados, mas não garante uma única instância da fachada.
- Singleton distribuído. O processo local é o escopo pedido.

### 5. Erros e rotas

Novos tratadores, no registro já existente:

| Exceção | HTTP | Corpo |
| --- | --- | --- |
| `InvalidWorkoutError` | 422 | `{"detail": "<mensagem da regra>"}` |
| `UserNotFoundError` e `WorkoutNotFoundError` | 404 | `{"detail": "Usuário não encontrado"}` ou `{"detail": "Treino não encontrado"}` |
| `PersistenceError` | 503 | `{"detail": "<public_message>"}` |

`GET /statistics/entities` conta usuários e depois treinos. A primeira falha define a mensagem: falha de usuários conserva o texto de usuários; falha de treinos usa o texto de treinos. O corpo não inclui SQL, caminho ou causa interna.

O identificador na URL precisa representar inteiro maior ou igual a 1. Valor não inteiro, zero ou negativo responde 422 e não é tratado como treino inexistente. A conversão de segmento textual da URL é normal; a regra de inteiro JSON estrito vale para `user_id` no corpo, sem impedir a leitura de `/workouts/1`.

O título OpenAPI passa de `Users API` para `Training Platform`. As rotas e o JSON de usuários não mudam.

### 6. Documentação acompanha o código existente

O ADR 0005 acompanha o primeiro PR que altera os contratos. O diagrama de projeto é atualizado nesse PR e novamente no PR da fachada, para representar apenas as classes já implementadas em cada etapa. Na documentação final, o diagrama de análise em `docs/05-analise.md` continua conceitual e inclui Treino, seu gerenciamento e a fronteira/controle apropriados. A fonte PlantUML e a imagem de projeto permanecem correspondentes.

A tabela de padrões recebe Singleton e Facade, com `FacadeSingletonController`, `UserService`, `WorkoutService` e o ADR 0005. Os repositórios e a seleção de persistência seguem a organização já existente, sem a reorganização prevista para a Sprint 4. Adapter, Template Method, Command e Memento não entram nesta change.

O diagrama geral de casos de uso separa o que esta sprint implementa do que a visão já deixou para depois: aplicativo mobile e agente de IA. Não entram funcionalidades sem registro na visão. UC01 é detalhado; UC03 e UC04 detalham cadastrar e atualizar treino. UC02 conserva o ID. Consultar, listar e excluir treino e consultar a contagem entram no diagrama geral com UC05–UC08, sem detalhamento completo. Wireframes TL01–TL03 documentam interface proposta e não criam frontend.

A origem da contagem no diagrama é o enunciado da Sprint 3, não a entrevista.

A validação da documentação entra no CI antes do arquivamento final. Ela faz parsing real de `openspec/config.yaml`, verifica tipos e conteúdo de contexto/regras, valida todas as specs e confere links locais, sem depender de uma change específica permanecer aberta. O carregamento efetivo por `openspec instructions` é demonstrado enquanto a change está ativa. O sucesso de `openspec validate --all` isoladamente não garante que a configuração seja válida. A versão de referência para reproduzir os comandos é `@fission-ai/openspec@1.14.3`, usada nesta revisão; alterações de versão precisam repetir as verificações.

## Risks / Trade-offs

- `PUT` sem descrição apaga a descrição anterior. O contrato fica simples e explícito; uma omissão acidental zera o texto.
- `public_message` com padrão preserva o 503 de usuários. Quem levantar `PersistenceError` precisa manter esse padrão ou informar a mensagem pública certa.
- A chave estrangeira exige o pragma em toda conexão. Uma conexão futura sem o pragma não aplicaria o vínculo no SQLite.
- A fachada única é por processo. Vários processos de servidor não compartilham a instância. Os dados SQLite continuam compartilhados pelo arquivo, como já ocorre com usuários.
- O título OpenAPI muda. Clientes que dependam do texto antigo precisam acompanhar esta mudança.

## Migration

Não há migração de dados além de `CREATE TABLE IF NOT EXISTS workouts` no arquivo já configurado. RAM continua volátil. Não se importa treino de outro formato.
