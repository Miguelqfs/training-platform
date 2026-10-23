# Confiabilidade do armazenamento

## Purpose

Comunicar indisponibilidade e garantir atomicidade e durabilidade no SQLite.

## Requirements

### Requirement: NF-CON-01 — Tratar falhas de persistência

Nas requisições de usuários afetadas por `sqlite3.Error` de leitura ou escrita, o sistema DEVE retornar HTTP 503 com exatamente `{"detail":"Armazenamento de usuários indisponível"}`, sem SQL ou caminhos internos. Conflitos de unicidade são erros de negócio (HTTP 409), não indisponibilidade. Falhas das requisições de treinos e da contagem estão em NF-CON-04.

**Prioridade:** Essencial

**Casos de uso:** UC01, UC02

#### Scenario: Banco indisponível

- **GIVEN** o banco iniciado e a tabela `users` removida para simular falha
- **WHEN** o cadastro ou a listagem de usuários é solicitado
- **THEN** ambas as operações retornam HTTP 503 com a mensagem especificada

### Requirement: NF-CON-02 — Garantir atomicidade do cadastro

Uma gravação SQLite malsucedida DEVE deixar 0 usuários novos e preservar os usuários anteriores.

**Prioridade:** Essencial

**Caso de uso:** UC01

#### Scenario: Falha após a inserção

- **GIVEN** 1 usuário no banco e um gatilho `AFTER INSERT` que aborta a gravação
- **WHEN** um segundo cadastro válido é enviado
- **THEN** retorna HTTP 503 e continuam exatamente 1 usuário na API e 1 linha no banco

### Requirement: NF-CON-03 — Preservar dados após reinicialização

Ao reiniciar a aplicação em modo SQLite usando o mesmo arquivo, 100% dos usuários confirmados DEVEM manter seus IDs e dados e continuar sujeitos às mesmas restrições de unicidade. O próximo cadastro DEVE receber um novo ID. Este requisito não se aplica ao modo RAM.

**Prioridade:** Essencial

**Casos de uso:** UC01, UC02

#### Scenario: Nova instância com o mesmo banco

- **GIVEN** 1 usuário confirmado no arquivo SQLite
- **WHEN** a aplicação é recriada com esse arquivo
- **THEN** lista o mesmo usuário com o mesmo ID, rejeita seu recadastro com HTTP 409 e atribui ID 2 a um novo usuário

A verificação recria a aplicação e suas conexões; não simula queda de energia nem corrupção de disco.

### Requirement: NF-CON-04 — Tratar falhas de persistência de treinos

Falhas SQLite nas operações de treinos DEVEM retornar HTTP 503 com `{"detail":"Armazenamento de treinos indisponível"}`, inclusive ao buscar o vínculo, sem detalhes internos. Na contagem, a mensagem DEVE corresponder à primeira consulta que falha: usuários antes de treinos. Usuário ausente ou violação de sua chave estrangeira DEVE retornar HTTP 404.

**Prioridade:** Essencial

**Casos de uso:** UC03, UC04, UC05, UC06, UC07, UC08

#### Scenario: Tabela de treinos indisponível

- **GIVEN** o banco iniciado e a tabela `workouts` removida para simular falha
- **WHEN** cadastro, listagem e contagem de treinos são solicitados
- **THEN** as três operações retornam HTTP 503 com a mensagem de treinos e o corpo não contém o caminho do arquivo

#### Scenario: Consulta individual, atualização e exclusão indisponíveis

- **GIVEN** a tabela `workouts` removida depois da inicialização para simular falha
- **WHEN** `GET /workouts/1`, `PUT /workouts/1` com corpo válido e `DELETE /workouts/1` são solicitados separadamente
- **THEN** as três operações retornam HTTP 503 com a mensagem de treinos, sem transformar a falha em HTTP 404

#### Scenario: Falha na busca do usuário vinculado

- **GIVEN** o repositório de usuários lança `PersistenceError` ao consultar o vínculo, mantendo disponível o repositório de treinos
- **WHEN** `POST /workouts/` recebe campos válidos
- **THEN** retorna HTTP 503 com a mensagem de treinos, preserva a causa internamente e grava 0 treinos

#### Scenario: Contagem com falha de usuários

- **GIVEN** a tabela `users` removida depois da inicialização
- **WHEN** `GET /statistics/entities` é solicitado
- **THEN** retorna HTTP 503 com exatamente `{"detail":"Armazenamento de usuários indisponível"}`

### Requirement: NF-CON-05 — Garantir atomicidade da gravação de treino

Criação, atualização ou exclusão SQLite de treino malsucedida DEVE reverter a respectiva mutação. Após a falha, todos os registros e a contagem DEVEM permanecer como antes da operação, com 0 alterações parciais confirmadas.

**Prioridade:** Essencial

**Casos de uso:** UC03, UC04, UC07, UC08

#### Scenario: Falha após a inserção

- **GIVEN** 1 usuário e 1 treino no banco e um gatilho `AFTER INSERT` em `workouts` que aborta a gravação
- **WHEN** um segundo cadastro válido de treino é enviado
- **THEN** retorna HTTP 503 e continuam exatamente 1 treino na API, 1 linha de treino e 1 usuário no banco

#### Scenario: Falha após a atualização

- **GIVEN** 1 usuário, 2 treinos com todos os campos conhecidos e um gatilho `AFTER UPDATE` em `workouts` que aborta a gravação
- **WHEN** um treino recebe nome e descrição novos por `PUT`
- **THEN** retorna HTTP 503; os dois treinos conservam todos os campos anteriores na API e no banco, o usuário permanece e o total continua 3

#### Scenario: Falha após a exclusão

- **GIVEN** 1 usuário, 2 treinos e um gatilho `AFTER DELETE` em `workouts` que aborta a gravação
- **WHEN** um treino é excluído por `DELETE`
- **THEN** retorna HTTP 503; os dois treinos e o usuário permanecem integralmente na API e no banco e o total continua 3

#### Scenario: Recuperação após remover a falha

- **GIVEN** uma criação, atualização ou exclusão falhou por um dos gatilhos acima
- **WHEN** o gatilho é removido e a operação válida é repetida
- **THEN** a operação é confirmada uma única vez e a contagem corresponde aos registros efetivamente persistidos

### Requirement: NF-CON-06 — Preservar treinos após reinicialização

Ao reiniciar a aplicação em modo SQLite usando o mesmo arquivo, 100% dos treinos confirmados DEVEM manter `id`, `user_id`, nome e descrição. O próximo cadastro DEVE receber um `id` ainda não usado. Este requisito não se aplica ao modo RAM.

**Prioridade:** Essencial

**Casos de uso:** UC03, UC06

#### Scenario: Nova instância com o mesmo banco

- **GIVEN** 1 usuário e 1 treino confirmado com `id` 1, `user_id` 1, nome `Peito` e descrição `supino`, no arquivo SQLite
- **WHEN** a aplicação é recriada com esse arquivo e outro treino válido é cadastrado
- **THEN** o primeiro treino conserva exatamente os quatro campos, o segundo recebe um novo `id` e a contagem total é 3

#### Scenario: Exclusão preservada após reinicialização

- **GIVEN** 1 usuário e treinos confirmados de `id` 1 e 2, sendo o treino 2 excluído com sucesso
- **WHEN** a aplicação é recriada com o mesmo arquivo e cadastra outro treino válido
- **THEN** o treino 2 continua ausente, o treino 1 conserva todos os campos, o novo treino recebe `id` 3 e a contagem total é 3

A verificação recria a aplicação e suas conexões; não simula queda de energia nem corrupção de disco.
