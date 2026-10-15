# Gerenciamento de usuários

## Purpose

Especificar o núcleo essencial implementado nas Sprints 1 e 2: cadastro, validação, listagem e seleção da persistência de usuários.

## Requirements

### Requirement: RF01 — Cadastrar usuário

O sistema DEVE permitir o cadastro de um usuário com login, e-mail, senha e papel de aluno ou administrador, gerando um ID inteiro único no armazenamento selecionado. O cliente não precisa fornecer o ID. Se o papel não for informado, DEVE usar aluno.

**Prioridade:** Essencial

**Caso de uso:** UC01

#### Scenario: Cadastro válido

- **GIVEN** uma coleção vazia
- **WHEN** `POST /users/` recebe `{"username":" maria ","email":"MARIA@example.com","password":"Abcdef12"}`
- **THEN** registra exatamente 1 usuário e retorna HTTP 201 com `{"id":1,"username":"maria","email":"maria@example.com","role":"student"}`

#### Scenario: Login ou e-mail duplicado

- **GIVEN** um usuário com login `Maria` e e-mail `maria@example.com`
- **WHEN** outro cadastro válido usa login ` MARIA ` ou e-mail `Maria@EXAMPLE.com`
- **THEN** a coleção continua com 1 usuário e retorna HTTP 409 com `detail: "Usuário ou e-mail já cadastrado"`

### Requirement: RF02 — Validar login

O sistema DEVE rejeitar login vazio, com mais de 12 caracteres após remover espaços externos ou contendo números, inclusive caracteres numéricos Unicode.

**Prioridade:** Essencial

**Caso de uso:** UC01

#### Scenario: Login vazio ou acima do limite

- **GIVEN** um login `""`, `"   "` ou com 13 caracteres
- **WHEN** o cadastro é enviado
- **THEN** não registra usuário e retorna HTTP 422 com erro de tamanho no campo `username`

#### Scenario: Login com número

- **GIVEN** um login `user1`, `user١` ou `user²`
- **WHEN** o cadastro é enviado com os demais campos válidos
- **THEN** não registra usuário e retorna HTTP 422 com `detail: "Login não pode conter números"`

#### Scenario: Limite aceito

- **GIVEN** login `aaaaaaaaaaaa` (12 caracteres) e demais campos válidos
- **WHEN** o cadastro é enviado
- **THEN** o sistema registra o usuário com HTTP 201

### Requirement: RF03 — Validar senha

O sistema DEVE exigir senha de 8 a 128 caracteres com pelo menos 3 categorias entre letras maiúsculas latinas, minúsculas latinas, dígitos e símbolos IAM permitidos. A senha não DEVE ser equivalente ao login ou e-mail após normalização sem diferenciar maiúsculas de minúsculas.

As categorias são `A-Z`, `a-z`, `0-9` e `!@#$%^&*()_+-=[]{}|'`. A senha não
é aparada. Símbolos fora dessa lista não contam como categoria IAM; não há regra
que proíba sua presença se as outras categorias forem suficientes. A política
adotada é a [padrão da AWS](https://docs.aws.amazon.com/pt_br/IAM/latest/UserGuide/id_credentials_passwords_account-policy.html),
com a equivalência a nome/e-mail adaptada ao usuário local no ADR 0003.

**Prioridade:** Essencial

**Caso de uso:** UC01

#### Scenario: Senha fora do tamanho

- **GIVEN** senha com 7 ou 129 caracteres e demais campos válidos
- **WHEN** o cadastro é enviado
- **THEN** não registra usuário e retorna HTTP 422 com `detail: "Senha deve ter de 8 a 128 caracteres"`

#### Scenario: Categorias insuficientes

- **GIVEN** senha `Abcdefgh` ou `Abcdefg?` (somente 2 categorias reconhecidas)
- **WHEN** o cadastro é enviado com os demais campos válidos
- **THEN** não registra usuário e retorna HTTP 422 com `detail: "Senha deve conter pelo menos 3 categorias: maiúsculas, minúsculas, números ou símbolos IAM"`

#### Scenario: Senha equivalente à identidade

- **GIVEN** login `Abcdefg!` e senha `aBCDEFG!`, que atende ao tamanho e às categorias
- **WHEN** o cadastro é enviado com e-mail válido
- **THEN** não registra usuário e retorna HTTP 422 com `detail: "Senha não pode ser igual ao login ou e-mail"`

#### Scenario: Senha no limite aceito

- **GIVEN** senha `Abcdef12` (8 caracteres) ou `Aa1` seguida de 125 letras `a` (128 caracteres), diferente da identidade
- **WHEN** o cadastro é enviado
- **THEN** o sistema registra o usuário com HTTP 201

### Requirement: RF04 — Listar usuários

O sistema DEVE listar os usuários cadastrados com ID, login, e-mail e papel.

**Prioridade:** Essencial

**Caso de uso:** UC02

#### Scenario: Lista disponível

- **GIVEN** uma coleção com 2 usuários
- **WHEN** `GET /users/` é solicitado
- **THEN** o sistema retorna HTTP 200 com 2 usuários

#### Scenario: Coleção vazia

- **GIVEN** nenhum usuário cadastrado
- **WHEN** `GET /users/` é solicitado
- **THEN** o sistema retorna HTTP 200 com lista de 0 usuários

### Requirement: RF05 — Selecionar persistência

O sistema DEVE permitir selecionar, no início da execução, armazenamento de usuários em RAM ou SQLite. `USER_STORAGE` aceita `memory` (padrão) ou `sqlite`; `USER_DATABASE` define o caminho SQLite (padrão `users.sqlite3`). Os argumentos explícitos de `create_app` têm precedência sobre as variáveis de ambiente. A durabilidade está especificada em NF-CON-03.

**Prioridade:** Essencial

**Casos de uso:** UC01, UC02

#### Scenario: Armazenamento em RAM

- **GIVEN** `USER_STORAGE=memory` ou configuração ausente
- **WHEN** a aplicação inicia e cadastra usuários
- **THEN** os usuários ficam disponíveis apenas na instância em execução

#### Scenario: Seleção SQLite

- **GIVEN** `USER_STORAGE=sqlite` e caminho válido em `USER_DATABASE`
- **WHEN** a aplicação inicia e cadastra um usuário
- **THEN** o cadastro usa o banco indicado na configuração

#### Scenario: Configuração inválida

- **GIVEN** `USER_STORAGE=unknown`
- **WHEN** a aplicação é inicializada
- **THEN** a inicialização falha com `ValueError: USER_STORAGE deve ser memory ou sqlite`

#### Scenario: Banco inacessível ou corrompido na inicialização

- **GIVEN** modo SQLite e caminho cujo diretório não existe ou arquivo que não é um banco SQLite válido
- **WHEN** a aplicação é inicializada
- **THEN** a inicialização falha com `PersistenceError`, preservando a causa, antes de atender requisições

### Requirement: RF06 — Validar e-mail

O sistema DEVE exigir e-mail válido no cadastro e armazená-lo sem espaços externos e em minúsculas.

**Prioridade:** Essencial

**Caso de uso:** UC01

#### Scenario: E-mail inválido

- **GIVEN** e-mail `not-an-email` e demais campos válidos
- **WHEN** o cadastro é enviado
- **THEN** não registra usuário e retorna HTTP 422 identificando o campo `email`

### Requirement: RF07 — Validar papel

O sistema DEVE aceitar somente os papéis `student` e `admin`, usando `student` quando o campo for omitido.

**Prioridade:** Essencial

**Caso de uso:** UC01

#### Scenario: Papel inválido

- **GIVEN** papel `trainer` e demais campos válidos
- **WHEN** o cadastro é enviado
- **THEN** não registra usuário e retorna HTTP 422 identificando o campo `role`

#### Scenario: Administrador cadastrado

- **GIVEN** login e e-mail únicos e senha válida
- **WHEN** o cadastro é enviado com `role: admin`
- **THEN** retorna HTTP 201 com `role: admin`
