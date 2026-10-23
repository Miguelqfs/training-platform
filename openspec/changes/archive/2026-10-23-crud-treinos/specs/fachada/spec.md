# Spec delta — fachada

## ADDED Requirements

### Requirement: RF16 — Operar pela fachada única

O sistema DEVE executar o cadastro e a listagem de usuários, o CRUD de treinos e a contagem de entidades por métodos de `FacadeSingletonController`. As rotas DEVEM usar essa fachada. A fachada DEVE delegar ao serviço de usuários e ao serviço de treinos do contexto recebido. Ela NÃO DEVE validar a regra de nome, executar SQL nem escolher o armazenamento.

**Prioridade:** Essencial

**Casos de uso:** UC01, UC02, UC03, UC04, UC05, UC06, UC07, UC08

#### Scenario: Cadastro de usuário pela fachada

- **GIVEN** o método de cadastro da fachada substituído por um dublê que registra a chamada e retorna um usuário
- **WHEN** `POST /users/` recebe um corpo válido
- **THEN** a resposta HTTP 201 vem do dublê e o repositório de usuários recebe 0 gravações diretas da rota

#### Scenario: Cadastro de treino pela fachada

- **GIVEN** o método de criar treino da fachada substituído por um dublê que retorna um treino fixo
- **WHEN** `POST /workouts/` é solicitado
- **THEN** a resposta é o treino do dublê e o repositório de treinos recebe 0 gravações diretas da rota

#### Scenario: Contagem pela fachada

- **GIVEN** `count_entities` substituído por um dublê que retorna 7
- **WHEN** `GET /statistics/entities` é solicitado
- **THEN** a resposta é HTTP 200 com `{"total": 7}` produzido a partir desse retorno

### Requirement: RF17 — Contar entidades cadastradas

`FacadeSingletonController.count_entities` DEVE retornar a soma inteira dos usuários, dos dois papéis, com os treinos do contexto recebido. `GET /statistics/entities` DEVE responder HTTP 200 com exatamente `{"total": N}`. Exclusão concluída reduz N; atualização e rejeição não o alteram.

**Prioridade:** Essencial

**Caso de uso:** UC08

#### Scenario: Soma de usuários e treinos

- **GIVEN** 1 usuário `student`, 1 usuário `admin` e 3 treinos no mesmo contexto
- **WHEN** `count_entities` é chamado para esse contexto
- **THEN** retorna o inteiro 5 e `GET /statistics/entities` responde `{"total": 5}`

#### Scenario: Coleções vazias

- **GIVEN** nenhum usuário e nenhum treino
- **WHEN** a contagem é solicitada
- **THEN** retorna o inteiro 0 e o HTTP 200 contém `{"total": 0}`

#### Scenario: Exclusão, atualização e rejeição

- **GIVEN** 2 usuários e 2 treinos, com total 4
- **WHEN** um treino é excluído, o outro é atualizado e um cadastro com nome vazio é rejeitado
- **THEN** o total fica 3 depois da exclusão e continua 3 depois da atualização e da rejeição

#### Scenario: Contagem no SQLite reiniciado

- **GIVEN** 2 usuários e 1 treino confirmados em um arquivo SQLite
- **WHEN** a aplicação é recriada com esse arquivo e a contagem é solicitada
- **THEN** `count_entities` retorna 3

### Requirement: RF18 — Isolar aplicações com uma fachada por processo

O sistema DEVE manter uma instância de `FacadeSingletonController` por processo, inclusive em construção concorrente, sem substituí-la em `create_app`. Cada aplicação DEVE ter contexto próprio. Dados DEVEM ser independentes em RAM e entre arquivos SQLite diferentes. O mesmo arquivo SQLite DEVE compartilhar dados intencionalmente entre aplicações. Criar uma aplicação NÃO DEVE redirecionar o contexto de outra.

**Prioridade:** Essencial

**Casos de uso:** UC01, UC03, UC08

#### Scenario: Identidade única

- **GIVEN** a primeira instância obtida da fachada
- **WHEN** outra chamada obtém a fachada e `create_app` é executado
- **THEN** as duas referências são o mesmo objeto e continuam sendo esse objeto depois de `create_app`

#### Scenario: Criação concorrente

- **GIVEN** um processo Python novo, sem instância da fachada criada
- **WHEN** chamadas concorrentes obtêm a fachada pela primeira vez
- **THEN** todas recebem 1 único objeto

#### Scenario: Aplicações RAM independentes

- **GIVEN** duas aplicações criadas com armazenamento em RAM
- **WHEN** a primeira cadastra 1 usuário e 1 treino
- **THEN** a segunda lista 0 usuários e 0 treinos e a primeira ainda lista os seus 2 registros

#### Scenario: Arquivos SQLite diferentes

- **GIVEN** duas aplicações SQLite com arquivos diferentes
- **WHEN** a primeira confirma 1 usuário e 1 treino
- **THEN** a segunda permanece com total 0 e o arquivo da primeira conserva os 2 registros

#### Scenario: Mesmo arquivo SQLite em aplicações simultâneas

- **GIVEN** duas aplicações ativas com contextos distintos e o mesmo arquivo SQLite
- **WHEN** a primeira confirma 1 usuário e 1 treino e a segunda consulta e atualiza esse treino
- **THEN** ambas observam os mesmos registros confirmados e total 2, e a primeira também observa a atualização sem que seu contexto seja substituído

#### Scenario: Primeira aplicação depois da segunda

- **GIVEN** a primeira aplicação já contém 1 usuário
- **WHEN** uma segunda aplicação é criada e usada
- **THEN** a primeira ainda lista esse usuário e aceita operações no próprio armazenamento
