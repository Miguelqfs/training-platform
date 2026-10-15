# Gerenciamento de usuários

## Purpose

Especificar o núcleo essencial implementado nas Sprints 1 e 2: cadastro, validação, listagem e seleção da persistência de usuários.

## Requirements

### Requirement: RF01 — Cadastrar usuário

O sistema DEVE permitir o cadastro de um usuário com login, e-mail, senha e papel de aluno ou administrador. Se o papel não for informado, DEVE usar aluno.

**Prioridade:** Essencial

**Caso de uso:** UC01

#### Scenario: Cadastro válido

- **GIVEN** login e e-mail ainda não cadastrados e campos válidos
- **WHEN** um cadastro é enviado a `POST /users/`
- **THEN** o sistema registra exatamente 1 usuário e retorna HTTP 201 com ID, login, e-mail e papel

#### Scenario: Login ou e-mail duplicado

- **GIVEN** um usuário já cadastrado com o mesmo login ou e-mail, sem diferenciar maiúsculas de minúsculas
- **WHEN** outro cadastro é enviado
- **THEN** o sistema não acrescenta usuário e retorna HTTP 409

### Requirement: RF02 — Validar login

O sistema DEVE rejeitar login vazio, com mais de 12 caracteres após remover espaços externos ou contendo números, inclusive caracteres numéricos Unicode.

**Prioridade:** Essencial

**Caso de uso:** UC01

#### Scenario: Login inválido

- **GIVEN** um login vazio, com 13 ou mais caracteres ou contendo número
- **WHEN** o cadastro é enviado
- **THEN** o sistema não registra usuário e retorna HTTP 422

#### Scenario: Limite aceito

- **GIVEN** um login válido de 12 caracteres e demais campos válidos
- **WHEN** o cadastro é enviado
- **THEN** o sistema registra o usuário com HTTP 201

### Requirement: RF03 — Validar senha

O sistema DEVE exigir senha de 8 a 128 caracteres com pelo menos 3 categorias entre letras maiúsculas latinas, minúsculas latinas, dígitos e símbolos IAM permitidos. A senha não DEVE ser equivalente ao login ou e-mail após normalização sem diferenciar maiúsculas de minúsculas.

**Prioridade:** Essencial

**Caso de uso:** UC01

#### Scenario: Senha fora da política

- **GIVEN** senha fora do limite de tamanho, com menos de 3 categorias ou equivalente ao login/e-mail
- **WHEN** o cadastro é enviado
- **THEN** o sistema não registra usuário e retorna HTTP 422

#### Scenario: Senha no limite aceito

- **GIVEN** uma senha de 8 ou 128 caracteres que atende às 3 categorias e difere da identidade
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

O sistema DEVE permitir selecionar, no início da execução, armazenamento de usuários em RAM ou SQLite. Em SQLite, usuários e IDs DEVEM permanecer disponíveis após reinicialização.

**Prioridade:** Essencial

**Casos de uso:** UC01, UC02

#### Scenario: Armazenamento em RAM

- **GIVEN** `USER_STORAGE=memory` ou configuração ausente
- **WHEN** a aplicação inicia e cadastra usuários
- **THEN** os usuários ficam disponíveis apenas na instância em execução

#### Scenario: Armazenamento permanente

- **GIVEN** `USER_STORAGE=sqlite` e caminho válido em `USER_DATABASE`
- **WHEN** a aplicação reinicia após um cadastro
- **THEN** o usuário e seu ID continuam disponíveis no banco
