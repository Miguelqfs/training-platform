# Gerenciamento de treinos

## Purpose
Definir o CRUD de planos de treino vinculados a usuários, seus campos, IDs e
persistência selecionável em RAM ou SQLite, preservando os contratos de usuários.

## Requirements

### Requirement: RF08 — Cadastrar treino

O sistema DEVE cadastrar um treino com nome, descrição e vínculo a exatamente um usuário já existente, gerando um `id` inteiro maior ou igual a 1. O cliente não fornece o `id`. Um usuário DEVE poder ter mais de um treino. Nomes iguais DEVEM ser aceitos. `POST /workouts/` DEVE retornar HTTP 201 com o treino criado.

**Prioridade:** Essencial

**Caso de uso:** UC03

#### Scenario: Cadastro válido

- **GIVEN** um usuário de `id` 1 e nenhum treino
- **WHEN** `POST /workouts/` recebe `{"user_id":1,"name":" Peito ","description":" supino "}`
- **THEN** retorna HTTP 201 com `{"id":1,"user_id":1,"name":"Peito","description":"supino"}` e a listagem contém esse único treino

#### Scenario: Vários treinos do mesmo usuário

- **GIVEN** um usuário existente
- **WHEN** dois cadastros válidos usam esse `user_id`
- **THEN** os dois treinos são registrados com `id` distintos e o mesmo `user_id`

#### Scenario: Nomes repetidos

- **GIVEN** um treino de nome `Peito` para um usuário existente
- **WHEN** outro cadastro válido repete o nome `Peito`, para o mesmo usuário ou para outro
- **THEN** o sistema registra o segundo treino e retorna HTTP 201

#### Scenario: Usuário inexistente

- **GIVEN** a coleção de treinos vazia e nenhum usuário com `id` 9
- **WHEN** um cadastro válido no restante usa `user_id` 9
- **THEN** retorna HTTP 404 com `detail: "Usuário não encontrado"` e a quantidade de treinos permanece 0

### Requirement: RF09 — Validar os campos do treino

O sistema DEVE exigir nome textual com 1 a 100 caracteres e descrição textual opcional com até 1.000 caracteres, após remover espaços externos; descrição omitida DEVE resultar em `""`. No cadastro, `user_id` DEVE ser inteiro JSON positivo, sem coerção. Campos desconhecidos e entradas inválidas DEVEM retornar HTTP 422 com o campo identificado, sem alterar registros. RF12 delimita os campos da atualização.

**Prioridade:** Essencial

**Casos de uso:** UC03, UC04

#### Scenario: Nome vazio ou acima do limite

- **GIVEN** um usuário existente e nome `""`, `"   "` ou com 101 caracteres
- **WHEN** o cadastro é enviado com os demais campos válidos
- **THEN** retorna HTTP 422 identificando o campo `name` e não registra treino

#### Scenario: Nome no limite

- **GIVEN** um usuário existente e nome com 1 ou 100 caracteres, fora os espaços externos
- **WHEN** o cadastro é enviado
- **THEN** retorna HTTP 201 com o nome já sem espaços externos

#### Scenario: Descrição omitida ou vazia

- **GIVEN** um usuário existente e corpo sem `description`, ou com `description` `""` ou `"   "`
- **WHEN** o cadastro é enviado com nome válido
- **THEN** retorna HTTP 201 com `description` `""`

#### Scenario: Descrição no limite e acima dele

- **GIVEN** um usuário existente
- **WHEN** a descrição tem 1.000 caracteres e, em outro pedido, 1.001 caracteres
- **THEN** o primeiro retorna HTTP 201 e o segundo retorna HTTP 422 identificando `description`, sem novo treino

#### Scenario: user_id inválido

- **GIVEN** `user_id` ausente, `null`, `true`, `false`, 0, -1, 1.0 ou `"1"`
- **WHEN** o cadastro é enviado com nome válido
- **THEN** retorna HTTP 422 identificando `user_id` e não registra treino

#### Scenario: Nome obrigatório e tipos de texto

- **GIVEN** corpo sem `name`, nome `null` ou numérico, ou descrição `null` ou numérica
- **WHEN** cadastro ou atualização é enviado com os demais campos válidos
- **THEN** retorna HTTP 422 identificando o campo correspondente, sem criar treino nem modificar um treino existente

#### Scenario: Campo desconhecido

- **GIVEN** um corpo válido acrescido de `"carga": 10`
- **WHEN** o cadastro é enviado
- **THEN** retorna HTTP 422 identificando `carga` e não registra treino

### Requirement: RF10 — Consultar treino

O sistema DEVE retornar um treino existente em `GET /workouts/{id}`. ID ausente no armazenamento DEVE retornar HTTP 404. ID que não seja inteiro maior ou igual a 1 DEVE retornar HTTP 422.

**Prioridade:** Essencial

**Caso de uso:** UC05

#### Scenario: Treino existente

- **GIVEN** um treino de `id` 1
- **WHEN** `GET /workouts/1` é solicitado
- **THEN** retorna HTTP 200 com esse treino

#### Scenario: Treino inexistente

- **GIVEN** nenhum treino de `id` 9
- **WHEN** `GET /workouts/9` é solicitado
- **THEN** retorna HTTP 404 com `detail: "Treino não encontrado"`

#### Scenario: ID de caminho inválido

- **GIVEN** a coleção de treinos vazia ou não
- **WHEN** o caminho usa `abc`, `0` ou `-1`
- **THEN** retorna HTTP 422 e a coleção permanece inalterada

### Requirement: RF11 — Listar treinos

O sistema DEVE listar todos os treinos ordenados por `id` crescente. A coleção vazia DEVE produzir HTTP 200 com `[]`.

**Prioridade:** Essencial

**Caso de uso:** UC06

#### Scenario: Lista ordenada

- **GIVEN** treinos com `id` 1 e 3
- **WHEN** `GET /workouts/` é solicitado
- **THEN** retorna HTTP 200 com os dois treinos nessa ordem de `id`

#### Scenario: Lista vazia

- **GIVEN** nenhum treino cadastrado
- **WHEN** `GET /workouts/` é solicitado
- **THEN** retorna HTTP 200 com lista de 0 treinos

### Requirement: RF12 — Atualizar treino

O sistema DEVE substituir somente nome e descrição de um treino existente, usando a normalização e os limites de RF09, preservando `id` e `user_id`, e retornar HTTP 200. `name` DEVE ser obrigatório; a omissão de `description` DEVE gravar `""`. Campo imutável presente, dado inválido ou treino inexistente DEVE conservar o registro anterior.

**Prioridade:** Essencial

**Caso de uso:** UC04

#### Scenario: Atualização válida

- **GIVEN** um treino de `id` 1, `user_id` 1, nome `Peito` e descrição `supino`
- **WHEN** `PUT /workouts/1` recebe `{"name":" Costas ","description":" remada "}`
- **THEN** retorna HTTP 200 com `{"id":1,"user_id":1,"name":"Costas","description":"remada"}`

#### Scenario: Descrição omitida

- **GIVEN** um treino com descrição `supino`
- **WHEN** `PUT` recebe somente um nome válido
- **THEN** retorna HTTP 200 com o novo nome e `description` `""`

#### Scenario: Campo imutável no corpo

- **GIVEN** um treino de `user_id` 1 e nome `Peito`
- **WHEN** `PUT` inclui `user_id` ou `id`, mesmo repetindo os valores já armazenados
- **THEN** retorna HTTP 422 e o treino continua com `user_id` 1 e nome `Peito`

#### Scenario: Campos inválidos na atualização

- **GIVEN** um treino existente com todos os campos conhecidos
- **WHEN** `PUT` omite `name`, envia nome com 101 caracteres, descrição com 1.001 caracteres ou um campo desconhecido
- **THEN** cada pedido retorna HTTP 422 identificando o campo e preserva integralmente o treino anterior e a contagem

#### Scenario: Atualização inválida ou treino inexistente

- **GIVEN** um treino de nome `Peito` e nenhum treino de `id` 9
- **WHEN** o treino existente recebe nome vazio e o `id` 9 recebe nome válido
- **THEN** o primeiro responde HTTP 422 e conserva `Peito`; o segundo responde HTTP 404 com `detail: "Treino não encontrado"`

### Requirement: RF13 — Excluir treino

O sistema DEVE excluir um treino existente e retornar HTTP 204 sem corpo. Consulta, atualização ou nova exclusão desse `id` DEVEM retornar HTTP 404. A exclusão DEVE deixar os demais treinos e todos os usuários inalterados.

**Prioridade:** Essencial

**Caso de uso:** UC07

#### Scenario: Exclusão

- **GIVEN** treinos de `id` 1 e 2 e um usuário vinculado
- **WHEN** `DELETE /workouts/1` é solicitado
- **THEN** retorna HTTP 204 sem corpo, a listagem contém somente o treino 2 e o usuário continua cadastrado

#### Scenario: Exclusão repetida ou inexistente

- **GIVEN** o treino 1 já foi excluído
- **WHEN** `DELETE /workouts/1` é solicitado outra vez
- **THEN** retorna HTTP 404 com `detail: "Treino não encontrado"` e a listagem não muda

#### Scenario: Consulta e atualização depois da exclusão

- **GIVEN** o treino 1 foi excluído com sucesso e o treino 2 continua cadastrado
- **WHEN** `GET /workouts/1` e `PUT /workouts/1` com corpo válido são solicitados
- **THEN** ambos retornam HTTP 404, o treino 1 não é recriado e o treino 2 conserva todos os campos

### Requirement: RF14 — Gerar identificadores sem reutilização

O sistema DEVE gerar o `id` do treino de forma crescente nos dois modos de armazenamento. Depois de uma exclusão, o próximo `id` DEVE ser maior do que qualquer `id` de cadastro confirmado naquela coleção. Duas criações concorrentes em RAM DEVEM receber `id` distintos. Não se exige sequência sem lacunas nem reserva permanente de IDs de transações revertidas.

**Prioridade:** Essencial

**Casos de uso:** UC03, UC07

#### Scenario: Exclusão do maior ID

- **GIVEN** treinos de `id` 1 e 2
- **WHEN** o treino 2 é excluído e um novo treino válido é cadastrado
- **THEN** o novo treino recebe `id` 3

#### Scenario: Exclusão de um ID anterior

- **GIVEN** treinos de `id` 1 e 2
- **WHEN** o treino 1 é excluído e um novo treino válido é cadastrado
- **THEN** o novo treino recebe `id` 3 e a listagem ordenada contém os `id` 2 e 3

#### Scenario: Criações concorrentes em RAM

- **GIVEN** armazenamento em RAM e um usuário existente
- **WHEN** duas criações válidas são concluídas de forma concorrente
- **THEN** os treinos resultantes têm 2 `id` distintos

### Requirement: RF15 — Persistir treinos no armazenamento selecionado

O sistema DEVE usar para treinos o modo e o arquivo selecionados para usuários. RAM nova DEVE começar vazia; reabertura SQLite DEVE preservar os dados existentes. Em banco legado sem treinos, a tabela DEVE ser criada vazia sem alterar usuários. Não há seletor separado de armazenamento.

**Prioridade:** Essencial

**Casos de uso:** UC03, UC06

#### Scenario: RAM volátil

- **GIVEN** uma aplicação em RAM com um treino confirmado
- **WHEN** outra aplicação em RAM é criada
- **THEN** a nova aplicação lista 0 treinos

#### Scenario: Mesmo arquivo SQLite

- **GIVEN** um treino confirmado no arquivo SQLite, vinculado a um usuário
- **WHEN** a aplicação é recriada com esse arquivo
- **THEN** a listagem contém o mesmo treino, com o mesmo `id` e o mesmo `user_id`

#### Scenario: Banco de usuários já existente

- **GIVEN** um arquivo SQLite que já contém 1 usuário e nenhuma tabela de treinos
- **WHEN** a aplicação é iniciada com esse arquivo e lista usuários e treinos
- **THEN** o usuário continua presente e a lista de treinos tem 0 itens
